#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动Hotcue生成器 V6.0
Rekordbox 原生数据驱动架构

优先级：Rekordbox PSSI 段落 > skill_hotcue_intelligence_v3 > librosa 物理探测
"""

from typing import Dict, Optional, Tuple, List
import sys
from pathlib import Path

# 导入配置加载器
try:
    from core.config_loader import load_dj_rules
except ImportError:
    def load_dj_rules(): return {} # Fallback

# 导入增强结构检测模块
sys.path.insert(0, str(Path(__file__).parent))

# 【V6.0】导入 Rekordbox 段落读取器
try:
    from core.rekordbox_phrase_reader import RekordboxPhraseReader, get_rekordbox_phrases
    REKORDBOX_PHRASE_ENABLED = True
except ImportError:
    REKORDBOX_PHRASE_ENABLED = False
    def get_rekordbox_phrases(*args, **kwargs):
        return []

try:
    from core.enhanced_structure_detector import detect_structure_enhanced, get_first_drop_time, get_intro_end_time, get_outro_start_time
    from skills.cueing_intelligence.scripts.vocal import calculate_vocal_alerts
    from skills.cueing_intelligence.scripts.pro import (
        professional_quantize, 
        get_pro_label, 
        analyze_track_grid_anchor,
        identify_mix_type
    )
except ImportError:
    # 如果导入失败，定义占位函数
    def detect_structure_enhanced(*args, **kwargs):
        return {'structure': {}, 'confidence': 0.5}
    def get_first_drop_time(structure):
        return None
    def get_intro_end_time(structure):
        return None
    def get_outro_start_time(structure):
        return None


def _bars_to_seconds(bars: float, bpm: float) -> float:
    """将 bars 转换为秒数"""
    if bpm <= 0:
        bpm = 120.0
    beat_duration = 60.0 / bpm
    return bars * 4 * beat_duration


def _quantize_to_phrase_boundary(
    timestamp: float,
    bpm: float,
    anchor: float = 0.0,
    snap_bars: int = 8
) -> float:
    """
    【V3.0 ULTRA+ 修复】量化时间点到乐句边界 (4/8/16/32 小节)

    专业 DJ 规则：所有混音点必须对齐到乐句边界
    - 4 小节 = 16 拍 = 短乐句
    - 8 小节 = 32 拍 = 标准乐句
    - 16 小节 = 64 拍 = 长乐句

    Args:
        timestamp: 原始时间点（秒）
        bpm: BPM
        anchor: 锚点时间
        snap_bars: 量化步长（小节数）

    Returns:
        对齐到乐句边界的时间点
    """
    if bpm <= 0 or timestamp < 0:
        return timestamp

    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4  # 1 小节的秒数

    # 计算从锚点开始的拍数
    beats_from_anchor = (timestamp - anchor) / beat_dur

    # 基础：拍子对齐 (Grid Alignment)
    quantized_beats = round(beats_from_anchor)

    # 乐句对齐 (Phrase Snapping)
    # snap_bars 小节 = snap_bars * 4 拍
    if snap_bars > 0:
        beats_per_phrase = snap_bars * 4
        quantized_beats = round(quantized_beats / beats_per_phrase) * beats_per_phrase

    # 还原到时间
    result = anchor + (quantized_beats * beat_dur)

    # 确保不为负
    return max(0.0, round(result, 3))


def _snap_to_nearest_beat(time: float, beat_times: List[float], tolerance: float = 0.5) -> float:
    """
    【V9.9 网格对齐协议】将时间点对齐到最近的beat
    
    Args:
        time: 原始时间点（秒）
        beat_times: 排序后的beat时间列表
        tolerance: 容差（秒），超过此值则不对齐
    
    Returns:
        对齐后的时间点
    """
    if not beat_times or time < 0:
        return time
    
    # 二分查找最近的beat
    import bisect
    idx = bisect.bisect_left(beat_times, time)
    
    candidates = []
    if idx > 0:
        candidates.append(beat_times[idx - 1])
    if idx < len(beat_times):
        candidates.append(beat_times[idx])
    
    if not candidates:
        return time
    
    # 选择最近的beat
    nearest_beat = min(candidates, key=lambda b: abs(b - time))
    
    # 如果距离太远，不对齐（可能是特殊情况）
    if abs(nearest_beat - time) > tolerance:
        return time
    
    return nearest_beat



def _generate_from_rekordbox_phrases(
    content_uuid: str,
    bpm: float,
    duration: float,
    vocal_regions: Optional[List] = None,
    dj_rules: Dict = None,
    **kwargs
) -> Optional[Dict]:
    """
    【V6.0 核心】基于 Rekordbox PSSI 段落数据生成标点
    
    用户习惯规则：
    - A 点：Intro 结束点或第一个 Up 起点（73.7% 在 Intro）
    - B 点：第一个能量变化点（Up/Buildup）（39.3% 在 Up）
    - C 点：Outro 起点或倒数第二个 Buildup
    - D 点：C 点后 8 bars 或歌曲结束
    - E 点：第一个 Chorus（高潮）
    """
    if not REKORDBOX_PHRASE_ENABLED or not content_uuid:
        return None
    
    reader = RekordboxPhraseReader()
    phrases = reader.get_phrases(content_uuid, bpm)
    
    if not phrases or len(phrases) < 3:
        return None  # 段落数据不足，回退到其他方法
    
    # 获取节拍持续时间与物理轴 (PQTZ 驱动)
    beat_dur = 60.0 / bpm
    anchor = reader.get_anchor_time(content_uuid)
    
    # 【规则集成】应用用户定义的 phrase_bars (用于 Fallback 偏移)
    phrase_bars = 16
    if dj_rules:
        phrase_bars = dj_rules.get('phrase_bars', 16)
        
    bar_N_dur = _bars_to_seconds(phrase_bars, bpm)
    bar_8_dur = _bars_to_seconds(8, bpm)
    
    # 【V9.7 特效词：真·对齐】 获取 Rekordbox 原始节拍网格
    # 如果有 PQTZ 数据，则使用非线性量化
    beat_grid = reader.get_beat_grid(content_uuid)
    beat_times = sorted([b['time'] for b in beat_grid]) if beat_grid else []
    
    # 【DEBUG】
    # print(f"[DEBUG] Beat grid count: {len(beat_times) if beat_times else 0}")
    if beat_times:
        pass
        # print(f"[DEBUG] First 5 beats: {beat_times[:5]}")
    
    # 【V9.8】规整人声区域数据
    if vocal_regions and isinstance(vocal_regions, str):
        import json
        try: vocal_regions = json.loads(vocal_regions)
        except: vocal_regions = []
        
    # ========== 专家建议点优先注入 (V9.2 Protocol) ==========
    custom_points = kwargs.get('custom_mix_points', {})
    suggested_in = custom_points.get('mix_in')
    suggested_out = custom_points.get('mix_out')
    
    # 【DEBUG】
    # print(f"[DEBUG] suggested_in BEFORE snap: {suggested_in}")
    
    # 【V9.9 网格对齐协议】对专家建议点进行grid snapping
    if suggested_in is not None and beat_times:
        suggested_in = _snap_to_nearest_beat(suggested_in, beat_times)
        # print(f"[DEBUG] suggested_in AFTER snap: {suggested_in}")
    if suggested_out is not None and beat_times:
        suggested_out = _snap_to_nearest_beat(suggested_out, beat_times)

    # ========== A/B 决策矩阵 V9.4 (对齐专家建议与用户习惯) ==========
    # 用户习惯：A=Start (Mix-In), B=Energy (Transition End)
    
    # 1. 首先确定 A 点 (Entrance)
    a_point = None
    phrase_label_a = "[Grid Sync]"
    
    # 优先级 0: Sorter 专家建议 (Sorter 的 mix_in_point 即为 A 点)
    if suggested_in is not None and suggested_in > 0:
        a_point = suggested_in
        phrase_label_a = "[Expert Advice]"
    
    # 优先级 1: Intro 起点
    if a_point is None:
        intro_p = reader.find_phrase(phrases, ["Intro"], "first")
        if intro_p:
            a_point = intro_p["time"]
            phrase_label_a = "[Rekordbox Intro Start]"
            
    # 优先级 2: 保底 (Anchor 或硬回溯)
    if a_point is None:
        a_point = anchor or 0.1
        phrase_label_a = "[Grid Anchor]"

    # 2. 确定 B 点 (Energy/Verse) - 必须在 A 之后
    b_point = None
    phrase_label_b = "[Grid Sync]"
    
    # 【V5.2 HOTFIX】确保 a_point 为有效数值
    if a_point is None:
        a_point = 0.1  # 强制回退
    
    # 预设：在 A 之后寻找第一个 Intro 结束、Buildup 或 Chorus
    # 寻找 A 之后第一个段落变化
    valid_phrases_after_a = [p for p in phrases if p["time"] > a_point + 1.0]
    
    # 优先级 1: Intro 结束
    intro_end = reader.find_phrase_end(phrases, "Intro")
    if intro_end and intro_end > a_point + 1.0 and intro_end < duration * 0.45:
        b_point = intro_end
        phrase_label_b = "[Rekordbox Intro End]"
    
    # 优先级 2: 第一个 Buildup/Up
    if b_point is None:
        main_energy = next((p for p in valid_phrases_after_a if p["kind"] in ["Buildup", "Up"]), None)
        if main_energy and main_energy["time"] < duration * 0.6:
            b_point = main_energy["time"]
            phrase_label_b = f"[Rekordbox {main_energy['kind']}]"
            
    # 优先级 3: 第一个 Chorus
    if b_point is None:
        chorus = next((p for p in valid_phrases_after_a if p["kind"] == "Chorus"), None)
        if chorus and chorus["time"] < duration * 0.5:
            b_point = chorus["time"]
            phrase_label_b = "[Rekordbox Chorus]"
            
    # 优先级 4: 强制步进 (16 bars)
    if b_point is None:
        b_point = a_point + bar_N_dur
        phrase_label_b = f"[+{phrase_bars} Bars]"

    # --- 最终校验与边界保护 ---
    if a_point < 0.1: a_point = 0.1
    if b_point >= duration: b_point = duration - 10.0
    
    # 【红线：A 绝对不能晚于 B】
    if a_point > b_point - 0.05:
        # 如果 A 比 B 还晚，说明这首歌没有前奏，或者 A 被设到了中间
        # 此时我们将 A 设为 B 的前一个八拍，或者 B 设为 A 之后
        if a_point > duration * 0.5: # A 在后面，说明是跳过前奏
            b_point = a_point + bar_8_dur
            phrase_label_b = "[Post-A Energy]"
        else: # A 在前面但被 B 超出，强制修正
            a_point = max(0.1, b_point - bar_8_dur)
            phrase_label_a = "[Auto-Pre-Start]"
    
    # ========== E 点：高潮 (Peak/DROP) V7.1 ==========
    e_point = None
    phrase_label_e = "[Grid Sync]"
    all_chorus = [p for p in phrases if p["kind"] == "Chorus"]
    waveform = reader.get_waveform(content_uuid)
    
    if all_chorus:
        e_point = all_chorus[0]["time"]
        phrase_label_e = "[Rekordbox Chorus]"
    
    if not e_point or e_point <= b_point or e_point > duration * 0.9:
        if waveform:
            changes = reader.calculate_energy_gradient(waveform, duration)
            candidates = [c for c in changes if duration * 0.35 <= c['time'] <= duration * 0.85 and c['gradient'] > 0]
            if candidates:
                e_point = candidates[0]['time']
                phrase_label_e = "[Waveform Peak]"
            else:
                start_idx = int(len(waveform) * 0.35)
                end_idx = int(len(waveform) * 0.85)
                sub_wf = waveform[start_idx:end_idx]
                if sub_wf:
                    peak_idx = start_idx + sub_wf.index(max(sub_wf))
                    e_point = (peak_idx / len(waveform)) * duration
                    phrase_label_e = "[Waveform Max]"
                else:
                    e_point = b_point + _bars_to_seconds(16, bpm)
                    phrase_label_e = "[Standard Drop]"
        else:
            e_point = b_point + _bars_to_seconds(16, bpm)
            phrase_label_e = "[Standard Drop]"

    # ========== C/D 点：出歌区间 (Outro 感知 + V9.2 保护) ==========
    c_point = None
    phrase_label_c = "[Grid Sync]"
    
    # 优先级 0: Sorter 专家建议 (V9.2 强效纠偏)
    if suggested_out is not None and suggested_out > duration * 0.4:
        c_point = suggested_out
        phrase_label_c = "[Expert Advice]"
    
    # 优先级 1: 【Phase 16】“双高峰 (Two-Drop)” 深度感知
    if c_point is None:
        choruses = [p for p in phrases if p["kind"] == "Chorus"]
        if len(choruses) >= 2:
            # 检测是否存在显著的“段落感”（两段 Chorus 间隔超过 30s）
            c1_end = reader.find_phrase_end_by_time(phrases, choruses[0]["time"])
            c2_start = choruses[1]["time"]
            
            if c2_start - c1_end > 30.0: # 存在明显的 Breakdown
                early_out = c1_end + _bars_to_seconds(8, bpm)
                if duration * 0.5 < early_out < duration * 0.8:
                    c_point = early_out
                    phrase_label_c = "[Two-Drop Early Mix-Out]"
    
    # 优先级 2: PSSI Outro (带 V9.2 中位线保护)
    if c_point is None:
        # 寻找所有 Outro，但过滤掉出现在曲目前 35% 的疑似噪音
        outros = [p for p in phrases if p["kind"] in ["Outro", "Fade"]]
        valid_outros = [p for p in outros if p["time"] > duration * 0.35]
        
        if valid_outros:
            c_point = valid_outros[0]["time"]
            phrase_label_c = f"[Rekordbox {valid_outros[0]['kind']}]"
        else:
            # 优先级 3: 最后一个 Down 段落
            downs = [p for p in phrases if p["kind"] in ["Down", "Breakdown"]]
            valid_downs = [p for p in downs if p["time"] > duration * 0.6]
            if valid_downs:
                c_point = valid_downs[-1]["time"]
                phrase_label_c = "[Rekordbox Down End]"
            else:
                # 优先级 4: 强制保底 (Outro 16 bars)
                c_point = duration - _bars_to_seconds(16, bpm)
                phrase_label_c = "[Standard Outro]"
            
    # 【强制 D 点可见】
    d_point = c_point + _bars_to_seconds(8, bpm)
    phrase_label_d = "[Outro +8 Bars]"
    if d_point >= duration: 
        d_point = duration - 0.2
        phrase_label_d = "[End Guard]"
    
    # ========== V9.8 专家级：人声避让 (Vocal Guard) ==========
    # 如果 C 点落在人声段，尝试向前寻找最近的器乐
    if vocal_regions:
        def is_vocal(t):
            for r in vocal_regions:
                try:
                    s, e = (r[0], r[1]) if isinstance(r, (list, tuple)) else (r.get('start', 0), r.get('end', 0))
                    if s - 0.5 <= t <= e + 0.5: return True
                except: continue
            return False
        
        if is_vocal(c_point):
            # 向前尝试回退最多 8 bars
            for i in range(1, 9):
                test_c = c_point - (beat_dur * i * 4) # 每次回退 1 bar
                if not is_vocal(test_c) and test_c > e_point + 10:
                    c_point = test_c
                    phrase_label_c += " (Vocal Guarded)"
                    # 同步移动 D 点
                    d_point = c_point + _bars_to_seconds(8, bpm)
                    break

    # ========== V9.7 物理防御：PQTZ 真·网格对齐 (Atomic Snapping) ==========
    # ========== V3.0 ULTRA+ 修复：添加乐句边界对齐 ==========
    import bisect

    def quantize_to_grid(t, snap_bars: int = 8):
        """
        量化时间点到节拍网格，并强制对齐到乐句边界

        Args:
            t: 原始时间点
            snap_bars: 量化步长（小节数），默认 8 小节

        Returns:
            对齐后的时间点
        """
        if t < 0:
            return 0.0

        # 如果有 beat_times，使用 PQTZ 网格
        if beat_times:
            # 第一步：对齐到最近的节拍
            idx = bisect.bisect_left(beat_times, t)
            if idx == 0:
                nearest_beat = beat_times[0]
            elif idx == len(beat_times):
                nearest_beat = beat_times[-1]
            else:
                before = beat_times[idx - 1]
                after = beat_times[idx]
                nearest_beat = before if (t - before) < (after - t) else after

            # 第二步：强制对齐到乐句边界 (8/16/32 小节)
            beats_from_anchor = (nearest_beat - anchor) / beat_dur
            if snap_bars > 0:
                beats_per_phrase = snap_bars * 4
                quantized_beats = round(beats_from_anchor / beats_per_phrase) * beats_per_phrase
                result = anchor + quantized_beats * beat_dur
            else:
                result = nearest_beat

            return round(max(0.0, result), 3)
        else:
            # Fallback: 线性计算
            beats_from_anchor = (t - anchor) / beat_dur
            quantized_beats = round(beats_from_anchor)
            if snap_bars > 0:
                beats_per_phrase = snap_bars * 4
                quantized_beats = round(quantized_beats / beats_per_phrase) * beats_per_phrase
            result = anchor + quantized_beats * beat_dur
            return round(max(0.0, result), 3)

    # ========== V7.1/9.2 防撞与语义对齐系统 ==========
    # 优先级：B > E > A > C > D
    # 确保 C/D 点绝不出现在 A/B 点之前，除非曲目极短
    raw_points = [
        ('B', b_point, 100),
        ('E', e_point, 90),
        ('A', a_point, 80),
        ('C', c_point, 70),
        ('D', d_point, 60)
    ]
    
    # 针对 17s 误报的二次暴力干预
    if raw_points[3][1] < raw_points[0][1] and duration > 60:
        # 如果 C 点在 B 点之前，说明 PSSI 选错了。强制向后推。
        new_c = max(raw_points[3][1], duration * 0.7)
        raw_points[3] = ('C', new_c, 70)
        raw_points[4] = ('D', new_c + _bars_to_seconds(8, bpm), 60)

    # ========== V3.0 Ultra+ 物理级：采样级过零检测 (Zero-Crossing Refinement) ==========
    def apply_zero_crossing_refinement(t, filePath):
        """在目标点 +/- 100ms 窗口内寻找零交叉点，防止跳转爆音"""
        if not filePath or not Path(filePath).exists(): return t
        try:
            import librosa
            # 加载 200ms 窗口的数据进行分析
            window_size = 0.1 # 100ms
            start_load = max(0, t - window_size)
            y, sr = librosa.load(filePath, sr=None, offset=start_load, duration=window_size * 2)
            if len(y) < 10: return t
            
            # 寻找绝对值最小的点（最接近零电平的点）
            # 目标位置在 y 的中间附近
            target_idx = int((t - start_load) * sr)
            search_range = int(0.02 * sr) # 在目标点 +/- 20ms 内精细搜索
            
            start_idx = max(0, target_idx - search_range)
            end_idx = min(len(y), target_idx + search_range)
            
            search_zone = y[start_idx:end_idx]
            if len(search_zone) == 0: return t
            
            # 寻找过零点
            min_val_idx = np.argmin(np.abs(search_zone))
            refined_t = start_load + (start_idx + min_val_idx) / sr
            return round(refined_t, 3)
        except:
            return t # 失败退回原点

    import numpy as np
    audio_path = kwargs.get('audio_file') or kwargs.get('file_path')

    final_points = {}
    last_time = -1.0
    for key, t, priority in sorted(raw_points, key=lambda x: x[1]):
        # 1. 防止点位重叠 (Collision Avoidance)
        if t <= last_time + 0.05: t = last_time + beat_dur
        
        # 2. V9.8 铁律：100% 节拍网格对齐 (PQTZ Snapping)
        # 不再运行过零点修正，因为那会产生 10-20ms 的视觉偏差
        t = quantize_to_grid(t)
            
        if t >= duration: t = duration - 0.05
        final_points[key] = t
        last_time = t

    # ========== 构建映射结果 V9.5 (语义对齐与习惯深度集成) ==========
    # ========== V3.0 ULTRA+ 修复：使用用户要求的 A-E 5点格式 ==========
    hotcues = {
        'A': {
            'Name': f"A: [IN] START {phrase_label_a}",
            'Start': final_points['A'],
            'Color': '0x0000FF',
            'Num': 0,
            'Type': 0,
            'PhraseLabel': phrase_label_a
        },
        'B': {
            'Name': f"B: [IN] ENERGY {phrase_label_b}",
            'Start': final_points['B'],
            'Color': '0xFFFF00',
            'Num': 1,
            'Type': 0,
            'PhraseLabel': phrase_label_b
        },
        'C': {
            'Name': f"C: [OUT] START {phrase_label_c}",
            'Start': final_points['C'],
            'Color': '0x0000FF',
            'Num': 2,
            'Type': 0,
            'PhraseLabel': phrase_label_c
        },
        'D': {
            'Name': f"D: [OUT] END {phrase_label_d if 'phrase_label_d' in locals() else '[Grid Sync]'}",
            'Start': final_points['D'],
            'Color': '0x0000FF',
            'Num': 3,
            'Type': 0,
            'PhraseLabel': phrase_label_d if 'phrase_label_d' in locals() else "[Grid Sync]"
        },
        'E': {
            'Name': f"E: [DROP] PEAK {phrase_label_e}",
            'Start': final_points['E'],
            'Color': '0xFF0000',
            'Num': 4,
            'Type': 0,
            'PhraseLabel': phrase_label_e
        }
    }

    # Memory Cues V9.6 (对齐用户习惯 Rule 5)
    memory_cues = []
    
    # 1. 检测是否可长混（A-B 段无人声）
    # 逻辑：如果 A点 到 B点 之间没有 vocal_regions 重叠，标记为 LONG MIX OK
    ab_has_vocal = False
    if vocal_regions:
        def _get_vocal_range(r):
            if isinstance(r, (list, tuple)): return r[0], r[1] if len(r) > 1 else r[0]
            elif isinstance(r, dict): return r.get('start', 0), r.get('end', 0)
            return 0, 0
        
        ab_has_vocal = any(
            (_get_vocal_range(r)[0] < final_points['B'] and _get_vocal_range(r)[1] > final_points['A'])
            for r in vocal_regions
        )
        
    if not ab_has_vocal:
        memory_cues.append({
            'Name': '[LONG MIX OK] 16 bars',
            'Start': final_points['A'], # 在 A 点标 Memory Cue
            'Num': -1,
            'Type': 0
        })
    
    # 2. 应急 Loop (Hotcue H 映射为 Memory Cue)
    raw_loop_t = final_points['D'] - _bars_to_seconds(4, bpm)
    memory_cues.append({
        'Name': '[EXIT] Emergency Loop',
        'Start': quantize_to_grid(raw_loop_t), # 同样强制对齐网格
        'Num': -1,
        'Type': 0
    })

    # 计算混音类型
    try:
        mix_type, mix_desc = identify_mix_type(final_points['A'], final_points['B'], bpm)
    except:
        mix_type = "Standard"
    
    return {
        'hotcues': hotcues,
        'memory_cues': memory_cues,
        'anchor': anchor, # 【修复核心】返回真实的 anchor 确保 Rekordbox 网格对齐！
        'bpm': bpm,
        'mix_type': mix_type,
        'source': 'rekordbox_pssi'
    }


def generate_hotcues(
    audio_file: str,
    bpm: Optional[float] = None,
    duration: Optional[float] = None,
    structure: Optional[Dict] = None,
    vocal_regions: Optional[List] = None,
    anchor: float = 0.0,
    **kwargs
) -> Dict:
    """
    自动生成高精度的 A/B/C/D Hotcue 点及 Memory Cues
    
    V6.0 架构：Rekordbox 原生数据驱动
    优先级：Rekordbox PSSI 段落 > skill_hotcue_intelligence_v3 > librosa 物理探测
    """
    if bpm is None or bpm <= 0:
        bpm = 120.0
    
    # 【V6.0 核心：优先使用 Rekordbox 段落数据】
    content_uuid = kwargs.pop('content_uuid', None)
    content_id = kwargs.pop('content_id', None)
    
    # 【V7.0】加载用户 DJ 规则
    dj_rules = load_dj_rules()
    
    if content_uuid:
        result = _generate_from_rekordbox_phrases(
            content_uuid=content_uuid,
            bpm=bpm,
            duration=duration or 180,
            vocal_regions=vocal_regions,
            dj_rules=dj_rules,  # 透传规则
            **kwargs
        )
        if result:
            return result
        else:
            # 【V3.0 ULTRA+ 修复】允许回退到物理探测
            # 如果 PSSI 数据不足，不报错，继续尝试其他方法
            print(f"  [WARN] PSSI 数据不足 (UUID: {content_uuid[:8]}...)，将尝试物理探测")
            # 不抛出错误，继续执行到 content_id 分支或物理探测分支

    if content_id:
        from skills.skill_hotcue_intelligence_v3 import generate_intelligent_cues_v3
        # 确保从 kwargs 中分离出 track_tags，避免 **kwargs 重复传递
        t_tags = kwargs.pop('track_tags', {})

        pro_result = generate_intelligent_cues_v3(
            content_id=str(content_id),
            duration=duration or 180,
            vocal_regions=vocal_regions,
            track_tags=t_tags,
            audio_file=audio_file, # 显式透传路径用于物理探测
            dj_rules=dj_rules,  # 透传规则
            **kwargs
        )
        
        if pro_result:
            # 【V6.0 强制重塑】即便来自 V3 引擎，也必须强制映射到 A-E 语义转换
            mapping = pro_result.get('cues', {})
            res_cues = {}
            
            # 定义 V6.0 标准映射
            v6_standard = {
                'A': {'Name': '[IN] START', 'Color': '0x0000FF'},
                'B': {'Name': '[IN] ENERGY', 'Color': '0xFFFF00'},
                'C': {'Name': '[OUT] START', 'Color': '0x0000FF'},
                'D': {'Name': '[OUT] END', 'Color': '0x0000FF'},
                'E': {'Name': '[DROP]', 'Color': '0xFF0000'}
            }
            
            # 准备过零点修正函数 (闭包或独立引用)
            # 注意：此处需要访问 apply_zero_crossing_refinement
            # 由于它在 _generate_from_rekordbox_phrases 内部，我将其上移到全局或此处重定义
            
            for char, standard in v6_standard.items():
                if char in mapping:
                    raw_t = mapping[char].get('Start', 0.0)
                    
                    # 【V3.0 Ultra+ 物理级】即便是 AI 路径，也强制执行采样过零检测
                    # 使用当前作用域可访问的路径
                    target_path = audio_file
                    
                    # 声明并应用过零点补丁 (直接内嵌逻辑以保持独立性)
                    t = raw_t
                    try:
                        import librosa
                        import numpy as np
                        window_size = 0.1 
                        start_load = max(0, t - window_size)
                        y, sr = librosa.load(target_path, sr=None, offset=start_load, duration=window_size * 2)
                        if len(y) >= 10:
                            target_idx = int((t - start_load) * sr)
                            search_range = int(0.02 * sr)
                            s_idx = max(0, target_idx - search_range)
                            e_idx = min(len(y), target_idx + search_range)
                            search_zone = y[s_idx:e_idx]
                            if len(search_zone) > 0:
                                min_val_idx = np.argmin(np.abs(search_zone))
                                t = round(start_load + (s_idx + min_val_idx) / sr, 3)
                    except: pass

                    res_cues[char] = {
                        'Name': standard['Name'],
                        'Start': t,
                        'Color': standard['Color'],
                        'Num': ord(char) - ord('A'),
                        'Type': 0,
                        'PhraseLabel': mapping[char].get('PhraseLabel', "[AI Structure Detected]")
                    }
            
            # 强制清空 F, G, H
            return {
                'hotcues': res_cues, 
                'memory_cues': pro_result.get('memory_cues', []), 
                'anchor': pro_result.get('anchor', 0.0),
                'bpm': bpm,
                'mix_type': pro_result.get('mix_type', 'Standard')
            }
            
    # 如果完全没有 ID，执行物理探测
    from skills.skill_pro_cueing import generate_pro_hotcues, analyze_track_grid_anchor
    
    # 【V7.3 专家强化】如果 anchor 丢失且有物理路径，强制尝试 librosa 探测
    if not anchor or anchor <= 0:
        try:
            import librosa
            import numpy as np
            y, sr = librosa.load(audio_file, duration=30) # 只加载前30秒探测
            anchor = analyze_track_grid_anchor(y, sr)
            print(f"  [物理探测] 自动捕获锚点 (Anchor): {anchor:.3f}s")
        except:
            anchor = 0.0

    pro_cues_list = generate_pro_hotcues(
        file_path=audio_file, 
        bpm=bpm, 
        duration=duration or 180, 
        structure=structure or {}, 
        anchor=anchor, 
        vocal_regions=vocal_regions,
        dj_rules=dj_rules,  # 透传规则
        **kwargs
    )
    
    # 【V6.0 强制转换】将物理探测结果转换为 A-E 5点
    v6_cues = {}
    label_map = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E'}
    # 习惯对齐映射
    user_name_map = {'A': '[Mix-In]', 'B': '[Start]', 'C': '[Outro]', 'D': '[End]', 'E': '[Peak]'}
    color_map = {'A': '0x0000FF', 'B': '0xFFFF00', 'C': '0x0000FF', 'D': '0x0000FF', 'E': '0xFF0000'}

    for cue in pro_cues_list:
        kind = cue.get('kind', 0)
        if kind in label_map:
            char = label_map[kind]
            p_label = cue.get('PhraseLabel', '[Physical Probe]')
            v6_cues[char] = {
                'Start': cue['time'],
                'Name': f"{user_name_map[char]} {p_label}",
                'Color': color_map[char],
                'PhraseLabel': p_label
            }
    
    # 物理探测下的 A-B 对齐补正 (B 回溯 8 bars)
    if 'A' in v6_cues and 'B' in v6_cues:
        b_time = v6_cues['B']['Start']
        bar_8_dur = _bars_to_seconds(8, bpm)
        # 强制执行 B 点前移 8 bars 给 A 点（专家习惯）
        v6_cues['A']['Start'] = max(0.5, b_time - bar_8_dur)
    
    # 如果缺少 B 点但有 A 点，基于 A 计算 B
    elif 'A' in v6_cues and 'B' not in v6_cues:
        a_time = v6_cues['A']['Start']
        v6_cues['B'] = {
            'Start': a_time + _bars_to_seconds(8, bpm),
            'Name': '[Start] [Auto-Energy]',
            'Color': '0xFFFF00'
        }
    
    # 计算混音类型
    mix_type, _ = identify_mix_type(v6_cues.get('A', {}).get('Start', 0), 
                                     v6_cues.get('B', {}).get('Start', 0), bpm)
    
    # 【专家修正】从原始结果中提取 memory_cues，防止泄漏
    mem_cues = []
    if content_uuid and 'result' in locals() and result:
        mem_cues = result.get('memory_cues', [])
    elif 'pro_cues_list' in locals() and isinstance(pro_cues_list, dict):
        mem_cues = pro_cues_list.get('memory_cues', [])
    
    return {
        'hotcues': v6_cues,
        'memory_cues': mem_cues,
        'bpm': bpm,
        'anchor': anchor,
        'mix_type': mix_type
    }

    

def hotcues_to_rekordbox_format(hotcues: Dict) -> Dict:
    """
    将Hotcue转换为Rekordbox XML格式 (V6.0 专家极简版)
    强制只允许 A-E 5个点位，确保 Deck 界面整洁。
    """
    res = {}
    
    # 兼容嵌套结构
    actual_hotcues = hotcues.get('hotcues', hotcues) if isinstance(hotcues, dict) else hotcues
    
    # 【V6.0 强制】只支持 A-E
    for char in ['A', 'B', 'C', 'D', 'E']:
        # 兼容不同来源的 Key 命名
        data = actual_hotcues.get(char) or actual_hotcues.get(f'hotcue_{char}')
        
        if data:
            # 优先使用数据中携带的颜色，否则使用 V6.0 标准色
            color_map = {
                'A': '0x0000FF', 'B': '0xFFFF00', 'C': '0x0000FF', 
                'D': '0x0000FF', 'E': '0xFF0000'
            }
            color = data.get('Color') or data.get('color') or color_map.get(char)
            
            res[char] = {
                'Name': f"{char}: {data.get('name') or data.get('Name') or 'Point'}",
                'Start': float(data.get('seconds') or data.get('Start') or data.get('time') or 0.0), 
                'Num': ord(char) - ord('A'), 
                'Type': 0,
                'Color': color
            }
            
    # 添加 Memory Cues (Num="-1")
    mem_list = hotcues.get('memory_cues', [])
    for i, mc in enumerate(mem_list[:3]): # 限制最多3个关键 Memory Cues
        name = mc.get('Name') or mc.get('name') or mc.get('comment') or 'Memory'
        start = mc.get('Start') or mc.get('time') or mc.get('seconds')
        if start is not None:
            res[f"MEM_{i}"] = {
                'Name': name,
                'Start': float(start),
                'Num': -1,
                'Type': 0
            }
            
    return res

