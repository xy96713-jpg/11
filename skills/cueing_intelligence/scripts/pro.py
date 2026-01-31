#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Cueing Skill (V1.0) - The "Pro DJ" Brain
Goal: Snapping AI cues to beatgrid and 8-bar phrases with Rekordbox parity.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

# 【V8.0】引入专家核心模块
try:
    from skills.unified_expert_core import VocalConflictEngine, PhraseQuantizer, CueStandard
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback (保持旧逻辑如果不幸导入失败，但理论上不应发生)

def _bars_to_second_impl(bars: float, beat_dur: float) -> float:
    if CORE_AVAILABLE:
        # 直接利用 PhraseQuantizer 换算但不依赖 BPM 参数 (这里参数是 beat_dur)
        # beat_dur = 60/bpm -> seconds = bars*4*beat_dur
        return bars * 4 * beat_dur
    return bars * 4 * beat_dur

def is_in_vocal_region(timestamp: float, vocal_regions: List[Tuple[float, float]], buffer: float = 0.5) -> bool:
    """检查特定时间点是否处于人声区域内 (Delegated to Core)"""
    if CORE_AVAILABLE:
        return VocalConflictEngine.is_active(timestamp, vocal_regions, buffer)
    
    # Legacy Fallback
    for r in vocal_regions:
        if isinstance(r, (list, tuple)):
            start, end = r[0], r[1]
        elif isinstance(r, dict):
            start, end = r.get('start', 0), r.get('end', 0)
        else:
            continue
        if (start - buffer) <= timestamp <= (end + buffer):
            return True
    return False

def find_nearest_instrumental_phrase(
    target_time: float, 
    bpm: float, 
    anchor: float, 
    vocal_regions: List[Tuple[float, float]],
    direction: int = 1, # 1 为向后找，-1 为向前找
    max_search_bars: int = 8,
    snap_to_phrase: int = 8
) -> float:
    """寻找最近的无声（器乐）段落起点（按 phrase 对齐）"""
    beat_dur = 60.0 / bpm
    phrase_dur = beat_dur * 4 * snap_to_phrase
    
    current_time = target_time
    for i in range(max_search_bars // snap_to_phrase + 1):
        test_time = professional_quantize(current_time + (i * direction * phrase_dur), bpm, anchor, snap_to_phrase)
        if not is_in_vocal_region(test_time, vocal_regions):
            return test_time
    return target_time # 找不到则返回原始建议点

def identify_mix_type(cue_a: float, cue_b: float, bpm: float) -> Tuple[str, str]:
    """
    分析 A-B 窗口长度，返回混音类型和描述。
    """
    if bpm <= 0: return "Unknown", "BPM 不详"
    
    beat_dur = 60.0 / bpm
    total_beats = (cue_b - cue_a) / beat_dur
    bars = total_beats / 4.0
    
    if bars > 24:
        return "Long Extended", f"{round(bars)} bars (超长混音/叠马)"
    elif bars > 12:
        return "Standard Mix", f"{round(bars)} bars (标准长混)"
    elif bars > 6:
        return "Short Blend", f"{round(bars)} bars (短混/平接)"
    else:
        return "Quick Cut", f"{round(bars)} bars (切歌/快切)"

def generate_emergency_loop(
    duration: float, 
    bpm: float, 
    anchor: float, 
    outro_start: float
) -> Optional[Dict]:
    """
    在歌曲末尾生成一个应急 Loop (HotCue H)
    """
    if bpm <= 0: return None
    beat_dur = 60.0 / bpm
    
    # 在 Outro 开始后或歌曲结束前 16 拍处设置
    loop_start_raw = max(outro_start, duration - 16 * beat_dur)
    loop_start = professional_quantize(loop_start_raw, bpm, anchor, snap_to_phrase=4)
    
    return {
        'kind': 8, # HotCue H
        'time': round(loop_start, 3),
        'name': "H: [Loop] Emergency (4b)",
        'loop_len': 16 # 16 beats = 4 bars
    }

def professional_quantize(
    timestamp: float, 
    bpm: float, 
    anchor: float = 0.0, 
    snap_to_phrase: int = 0
) -> float:
    """
    将时间戳量化到最接近的拍子 (Delegated to Core)
    """
    if CORE_AVAILABLE:
        # Core 接受 force_snap_bars 参数
        return PhraseQuantizer.quantize(
            timestamp=timestamp, 
            bpm=bpm, 
            anchor=anchor, 
            force_snap_bars=snap_to_phrase if snap_to_phrase > 0 else None
        )

    # Legacy Fallback
    if bpm <= 0: return timestamp
    
    beat_dur = 60.0 / bpm
    
    # 1. 基础拍子对齐 (Grid Alignment)
    beats_from_start = (timestamp - anchor) / beat_dur
    quantized_beats = round(beats_from_start)
    
    # 2. Phrase 对齐 (Phrase Snapping)
    if snap_to_phrase > 0:
        beats_per_phrase = snap_to_phrase * 4
        quantized_beats = round(quantized_beats / beats_per_phrase) * beats_per_phrase
        
    return max(0.0, anchor + (quantized_beats * beat_dur))

def get_pro_label(kind: int, phrase_name: str = "") -> str:
    """获取专业打点标签"""
    mapping = {
        1: "A: [Mix-In] ",
        2: "B: [Start] ",
        3: "C: [Outro] ",
        4: "D: [End] ",
        5: "E: [Peak] ",
        6: "F: [Bridge] ",
        7: "G: [Build] ",
        8: "H: [Loop] "
    }
    prefix = mapping.get(kind, f"Cue {kind}: ")
    return f"{prefix}{phrase_name}".strip()

def analyze_track_grid_anchor(y: np.ndarray, sr: int) -> float:
    """使用 librosa 探测歌曲的第一拍作为 Anchor"""
    try:
        import librosa
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        if len(beats) > 0:
            beat_times = librosa.frames_to_time(beats, sr=sr)
            return float(beat_times[0])
    except:
        pass
    return 0.0

def generate_pro_hotcues(
    file_path: str,
    bpm: float,
    duration: float,
    structure: Dict,
    anchor: float = 0.0,
    vocal_regions: List[Tuple[float, float]] = None,
    **kwargs
) -> List[Dict]:
    """
    根据 AI 结构生成专业量化且避开人声冲突的标点数据
    """
    beat_dur = 60.0 / bpm
    vocal_regions = vocal_regions or []
    # 安全提取结构化数据
    struct_data = structure or {}
    analysis = struct_data.get('analysis', {})
    struct = struct_data.get('structure', {})
    
    # 【V7.0】从规则中获取 phrase_bars (默认 8 bars 用于量化)
    dj_rules = kwargs.get('dj_rules', {}) or {}
    phrase_bars = dj_rules.get('phrase_bars', 16)
    # 专业量化基准：通常为 phrase_bars 的一半或 8 bars
    # 如果用户设置为 32 bar，则对齐到 16 bar
    # 如果用户设置为 16 bar，则对齐到 8 bar
    snap_bars = int(phrase_bars / 2) if phrase_bars >= 16 else 8
    
    cues = []
    
    # 【V9.2 Protocol】优先使用专家建议点
    custom_points = kwargs.get('custom_mix_points', {})
    suggested_in = custom_points.get('mix_in')
    suggested_out = custom_points.get('mix_out')

    # --- 1. 寻找起点 B (Main Energy / Verse Start) ---
    # 策略：如果提供建议点，强制作为 B 点；
    # 否则寻找第一个 Buildup/Chorus 或按 B = A + N bars 计算
    raw_b = None
    if suggested_in is not None and suggested_in > 0:
        raw_b = suggested_in
    else:
        # Fallback 寻找第一个能量段落
        raw_b = struct.get('drop', (0.0, 0.0))[0]
        if raw_b <= 0:
            raw_b = analysis.get('mix_in_point', analysis.get('recommended_mix_in', 64 * beat_dur))

    cue_b = professional_quantize(raw_b, bpm, anchor, snap_to_phrase=snap_bars if suggested_in is None else 0)
    cues.append({'kind': 2, 'time': round(cue_b, 3), 'name': get_pro_label(2, "Verse/Main")})

    # --- 2. 补全 A (Mix-In Start) ---
    # 策略：B 点回退 phrase_bars (16/32 bars)
    cue_a = max(0.0, cue_b - _bars_to_second_impl(phrase_bars, beat_dur))
    # 如果 A 进入了人声，向后找最近的器乐
    if is_in_vocal_region(cue_a, vocal_regions):
        cue_a = find_nearest_instrumental_phrase(cue_a, bpm, anchor, vocal_regions, direction=1)
    
    # 确保 A < B
    if cue_a >= cue_b: cue_a = max(0.0, cue_b - 8 * beat_dur)
    
    cues.append({'kind': 1, 'time': round(cue_a, 3), 'name': get_pro_label(1, "Intro / Mix-In")})
    
    # --- 3. 寻找 Drop E ---
    # 策略：在 B 之后的高能量点
    raw_e = struct.get('drop', (0.0, 0.0))[0]
    if raw_e <= cue_b:
        raw_e = analysis.get('drop_point', cue_b + (32 * beat_dur))
    
    cue_e = professional_quantize(raw_e, bpm, anchor)
    if cue_e <= cue_b: cue_e = cue_b + (32 * beat_dur)
        
    cues.append({'kind': 5, 'time': round(cue_e, 3), 'name': get_pro_label(5, "Drop / Peak")})
        
    # --- 4. 寻找出标点 C (Mix-Out Start) ---
    # 策略：优先使用建议点，否则使用 Outro 探测
    raw_c = None
    if suggested_out is not None and suggested_out > cue_e:
        raw_c = suggested_out
        snap_unit = 0 # 专家建议点只做物理对齐(Grid)，不强行跳转Phrase
    else:
        raw_c = struct.get('outro', (0.0, 0.0))[0]
        if raw_c <= cue_e:
            raw_c = analysis.get('mix_out_point', analysis.get('recommended_mix_out', duration * 0.85))
        snap_unit = 8
        
    cue_c = professional_quantize(raw_c, bpm, anchor, snap_to_phrase=snap_unit)
    # 出歌点避让
    if is_in_vocal_region(cue_c, vocal_regions):
        cue_c = find_nearest_instrumental_phrase(cue_c, bpm, anchor, vocal_regions, direction=-1)
    
    # 强制约束：C > E
    min_c = cue_e + (16 * beat_dur)
    if cue_c < min_c:
        cue_c = professional_quantize(min_c, bpm, anchor, snap_to_phrase=8)
        
    cues.append({'kind': 3, 'time': round(cue_c, 3), 'name': get_pro_label(3, "Outro / Mix-Out")})
    
    # --- 5. 结尾点 D ---
    cue_d = professional_quantize(duration, bpm, anchor)
    # 确保 D > C
    if cue_d <= cue_c: cue_d = duration
    cues.append({'kind': 4, 'time': round(cue_d, 3), 'name': get_pro_label(4, "End")})
    
    # H: Emergency Loop
    hc_h = generate_emergency_loop(duration, bpm, anchor, cue_c)
    if hc_h:
        cues.append(hc_h)
    
    return cues

if __name__ == "__main__":
    # Test
    test_bpm = 126.0
    test_anchor = 0.123
    raw_point = 8.1
    
    print(f"BPM: {test_bpm}, Anchor: {test_anchor}")
    print(f"Raw Point: {raw_point}s")
    print(f"Beat Quantized: {professional_quantize(raw_point, test_bpm, test_anchor)}s")
    print(f"Phrase Quantized (8 Bar): {professional_quantize(raw_point, test_bpm, test_anchor, snap_to_phrase=8)}s")
