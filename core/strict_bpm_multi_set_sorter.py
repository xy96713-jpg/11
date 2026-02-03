#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格BPM多Set排序工具
为"流行Boiler Room"等歌单生成多个set，严格限制相邻歌曲BPM跨度不超过12
使用librosa深度分析每首歌曲
"""

import os
import sys
import hashlib
import yaml
from pathlib import Path

# Import atomicity# 导入质量监控
try:
    from conflict_monitor_overlay import generate_radar_report
except ImportError:
    def generate_radar_report(tracks): return "无法生成雷达报告"

# 【V33.0】导入母带级语义分析核心
try:
    from core.mastering_core import MasteringAnalyzer
    MASTERING_ANALYZER = MasteringAnalyzer()
    HAS_MASTERING_CORE = True
except ImportError:
    HAS_MASTERING_CORE = False
    MASTERING_ANALYZER = None
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.cache_manager import load_cache, save_cache_atomic
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# 使用MCP rekordbox-mcp
sys.path.insert(0, str(Path(__file__).parent / "rekordbox-mcp"))

try:
    from rekordbox_mcp.database import RekordboxDatabase
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保rekordbox-mcp已正确安装")
    sys.exit(1)

# 导入专业排序算法（可选）
try:
    from professional_dj_set_sorter_standard import (
        get_key_compatibility,
        get_bpm_compatibility,
        professional_dj_sort_improved
    )
except ImportError:
    # 如果导入失败，使用简化版本
    def get_key_compatibility(key1: str, key2: str) -> float:
        """简化的key兼容性计算"""
        if not key1 or not key2 or key1 == "未知" or key2 == "未知":
            return 0.5
        # 简单的兼容性判断
        return 1.0 if key1 == key2 else 0.3
    
    def get_bpm_compatibility(bpm1: float, bpm2: float) -> float:
        """简化的BPM兼容性计算"""
        if bpm1 <= 0 or bpm2 <= 0:
            return 0.5
        diff = abs(bpm1 - bpm2)
        return max(0.0, 1.0 - diff / 20.0)
    
    def professional_dj_sort_improved(*args, **kwargs):
        """占位函数"""
        return [], []

# 导入librosa用于深度分析
try:
    import librosa
    import numpy as np
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    np = None
    print("警告: librosa未安装，将使用数据库中的BPM数据")
    print("安装命令: pip install librosa numpy")

# 可选：响度（LUFS）分析
try:
    import pyloudnorm as pyln  # type: ignore
    HAS_PYLOUDNORM = True
except Exception:
    pyln = None
    HAS_PYLOUDNORM = False


def _pct(values: "np.ndarray", q: float) -> float:
    """numpy 百分位的安全封装。"""
    if values is None or len(values) == 0:
        return 0.0
    q = max(0.0, min(100.0, float(q)))
    try:
        return float(np.percentile(values, q))
    except Exception:
        return float(np.median(values))


def analyze_mix_metrics_light(y: "np.ndarray", sr: int, bpm: float, beat_times: "np.ndarray | list", file_path: str = "") -> Dict:
    """
    轻量但对DJ实务很有价值的新增维度（通用曲风）：
    - sub_bass_level / kick_drum_power / sub_bass_presence（低频与底鼓）
    - kick_hardness（底鼓硬度/起音）
    - loudness_lufs / dynamic_range_db / crest_factor（音质与响度）
    - tonal_balance / brightness / spectral_cutoff（频段平衡与音色截断）
    - busy_score / onset_density（编曲繁忙度）
    - language（语言识别：华语/外语）
    - mixable_windows（可混音窗口）
    """
    res: Dict = {}
    if y is None or sr <= 0 or y.size == 0:
        return res

    # ===== 0) Language Detection (Metadata & Filename Based) =====
    try:
        lang = "English"  # 默认
        base_name = os.path.basename(file_path).lower()
        # 简单正则：包含中文字符则判定为华语
        import re
        if re.search(r'[\u4e00-\u9fa5]', base_name):
            lang = "Chinese"
        res["language"] = lang
    except Exception:
        res["language"] = "Unknown"

    # ===== 0.5) True Start Detection (Silence & Downbeat Alignment) =====
    try:
        # 寻找真正的起始位置：第一个明显的能量爆发点
        # 使用 librosa.effects.trim 的内部逻辑或简单阈值
        _, trim_idx = librosa.effects.trim(y, top_db=30)
        res["true_start_sec"] = float(trim_idx[0] / sr)
    except Exception:
        res["true_start_sec"] = 0.0

    # ===== 1) Dynamic Range & Crest Factor =====
    try:
        hop = 512
        frame_length = 2048
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)[0]
        rms_db = librosa.amplitude_to_db(rms + 1e-9, ref=np.max)
        # 用 95-10 分位作为动态范围估计（dB）
        dynamic_range_db = _pct(rms_db, 95) - _pct(rms_db, 10)
        res["dynamic_range_db"] = float(dynamic_range_db)
        
        # Crest Factor: Peak / RMS
        peak = np.max(np.abs(y))
        avg_rms = np.sqrt(np.mean(y**2))
        res["crest_factor"] = float(peak / (avg_rms + 1e-9))
    except Exception:
        pass

    # ===== 2) LUFS & Brick-wall Check =====
    try:
        if HAS_PYLOUDNORM and pyln is not None:
            meter = pyln.Meter(sr)
            lufs = float(meter.integrated_loudness(y.astype(np.float64)))
            res["loudness_lufs"] = lufs
            dr = float(res.get("dynamic_range_db", 0.0) or 0.0)
            # Brick-walled: 响度高且动态极小
            res["is_brick_walled"] = bool((dr > 0 and dr < 5.0) and (lufs > -8.0))
        else:
            res["loudness_lufs"] = None
            res["is_brick_walled"] = None
    except Exception:
        pass

    # ===== 3) Sub-bass / Kick / Kick Hardness =====
    try:
        S = np.abs(librosa.stft(y=y, n_fft=2048, hop_length=512)) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        total = float(np.sum(S)) + 1e-12

        sub_mask = (freqs >= 20) & (freqs <= 60)
        kick_mask = (freqs >= 60) & (freqs <= 120)
        sub_energy_frames = np.sum(S[sub_mask, :], axis=0)
        
        res["sub_bass_level"] = float(np.clip(np.sum(sub_energy_frames) / total, 0.0, 1.0))
        
        # Sub-bass Presence: 低频持续时间占比
        sub_th = np.percentile(sub_energy_frames, 70)
        res["sub_bass_presence"] = float(np.mean(sub_energy_frames > sub_th))

        # Kick Hardness: 提取低频能量的起音速度 (Attack)
        # 简单实现：观察低频能量上升沿的陡峭度
        low_onset = librosa.onset.onset_strength(S=S[kick_mask, :], sr=sr)
        res["kick_hardness"] = float(np.clip(_pct(low_onset, 90), 0.0, 1.0))
        
        # kick_drum_power
        low_band = np.sum(S[kick_mask, :], axis=0)
        low_band_n = low_band / (np.max(low_band) + 1e-9)
        res["kick_drum_power"] = float(np.clip(_pct(low_band_n, 90), 0.0, 1.0))
    except Exception:
        pass

    # ===== 5) Tonal Balance & Spectral Cutoff & Stereo Width =====
    try:
        if "S" not in locals():
            S = np.abs(librosa.stft(y=y, n_fft=2048, hop_length=512)) ** 2
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        
        # Spectral Cutoff: 95% 能量所在的频率
        spec_rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr, roll_percent=0.95)[0]
        res["spectral_cutoff_hz"] = float(np.mean(spec_rolloff))
        # 如果截断频率低于 16kHz，可能是低码率或假无损
        res["is_possibly_fake_lossless"] = bool(res["spectral_cutoff_hz"] < 16000)

        # Stereo Width Detection (仅在提供 file_path 且能读取时)
        res["stereo_width"] = 0.5 # 默认值
        if file_path and os.path.exists(file_path):
            try:
                # 只加载前 30s 的双声道音频进行分析，避免内存溢出
                y_stereo, _ = librosa.load(file_path, sr=sr, mono=False, duration=30.0)
                if y_stereo.ndim == 2:
                    # 计算左右声道相关性
                    # correlation = 1 表示完全单声道，correlation = 0 表示完全独立
                    left = y_stereo[0]
                    right = y_stereo[1]
                    if left.size > 0 and right.size > 0:
                        corr = np.corrcoef(left, right)[0, 1]
                        res["stereo_width"] = float(np.clip(1.0 - corr, 0.0, 1.0))
                else:
                    # 已经是单声道文件
                    res["stereo_width"] = 0.0
            except:
                pass

        total = float(np.sum(S)) + 1e-12
        low_mask = (freqs >= 20) & (freqs < 250)
        mid_mask = (freqs >= 250) & (freqs < 2000)
        high_mask = (freqs >= 2000) & (freqs <= 8000)
        res["tonal_balance_low"] = float(np.clip(np.sum(S[low_mask, :]) / total, 0.0, 1.0))
        res["tonal_balance_mid"] = float(np.clip(np.sum(S[mid_mask, :]) / total, 0.0, 1.0))
        res["tonal_balance_high"] = float(np.clip(np.sum(S[high_mask, :]) / total, 0.0, 1.0))
        
        centroid = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
        res["brightness"] = float(np.clip((np.mean(centroid) - 300.0) / 4200.0, 0.0, 1.0))
    except Exception:
        pass

    # ===== 6) Arrangement Busy-ness（编曲繁忙度）=====
    try:
        # onset envelope（归一化后用于“繁忙度”估计）
        hop = 512
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        if onset_env is not None and onset_env.size > 0:
            onset_env_n = onset_env / (np.max(onset_env) + 1e-9)
            # onsets per second
            onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop, backtrack=False, units="time")
            duration = float(len(y)) / float(sr)
            onset_density = float(len(onsets) / max(1e-6, duration))
            res["onset_density"] = onset_density
            # 瞬态密度：onset_env 90分位（0-1）
            res["transient_density"] = float(np.clip(_pct(onset_env_n, 90), 0.0, 1.0))
            # busy_score：综合（更偏重瞬态密度，其次看onset密度）
            # onset_density 经验上 0.5~4.0 之间较常见
            od_n = float(np.clip((onset_density - 0.5) / 3.5, 0.0, 1.0))
            res["busy_score"] = float(np.clip(0.65 * res["transient_density"] + 0.35 * od_n, 0.0, 1.0))
    except Exception:
        pass

    # ===== 7) Mixable Windows（可混音窗口，轻量规则）=====
    # 目标：给出“相对稳定/瞬态较低”的时间段，方便选择混入/混出窗口
    try:
        hop = 512
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
        rms_n = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-9)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        onset_n = onset_env / (np.max(onset_env) + 1e-9) if onset_env is not None and onset_env.size else None

        if onset_n is not None and onset_n.size == rms_n.size:
            times = librosa.frames_to_time(np.arange(len(rms_n)), sr=sr, hop_length=hop)
            # 低瞬态 + 非静音：适合长混
            onset_th = float(np.percentile(onset_n, 35))
            min_len = 8.0
            windows = []
            in_seg = False
            s0 = 0.0
            for t, onv, rv in zip(times, onset_n, rms_n):
                ok = (onv <= onset_th) and (rv >= 0.12)
                if ok and not in_seg:
                    in_seg = True
                    s0 = float(t)
                if in_seg and not ok:
                    e0 = float(t)
                    if e0 - s0 >= min_len:
                        # score：越低瞬态越好
                        seg_idx = (times >= s0) & (times <= e0)
                        seg_on = onset_n[seg_idx]
                        score = 1.0 - float(np.mean(seg_on)) if seg_on.size else 0.5
                        windows.append((round(s0, 2), round(e0, 2), round(float(np.clip(score, 0.0, 1.0)), 3)))
                    in_seg = False
            if in_seg:
                e0 = float(times[-1])
                if e0 - s0 >= min_len:
                    seg_idx = (times >= s0) & (times <= e0)
                    seg_on = onset_n[seg_idx]
                    score = 1.0 - float(np.mean(seg_on)) if seg_on.size else 0.5
                    windows.append((round(s0, 2), round(e0, 2), round(float(np.clip(score, 0.0, 1.0)), 3)))

            # 只保留最多 6 段（按 score 排序，避免缓存膨胀）
            if windows:
                windows.sort(key=lambda x: x[2], reverse=True)
                res["mixable_windows"] = windows[:6]
                res["mixable_windows_count"] = int(len(res["mixable_windows"]))
    except Exception:
        pass

    # ===== 8) Mashup V3-PRO 进阶特性 (频谱/律动/纹理/氛围) =====
    try:
        from skills.skill_v3_features import (
            calculate_spectral_bands, calculate_swing_dna, 
            calculate_energy_curve, calculate_timbre_texture,
            calculate_vibe_tags
        )
        res["spectral_bands"] = calculate_spectral_bands(y, sr)
        if len(beat_times) > 0:
            res["swing_dna"] = calculate_swing_dna(np.array(beat_times))
        res["energy_curve"] = calculate_energy_curve(y, sr, window_sec=8.0)
        res["timbre_texture"] = calculate_timbre_texture(y, sr)
        
        # 注入情感氛围与深度标签
        energy_val = res.get("energy", 50) / 100.0
        res["vibe_analysis"] = calculate_vibe_tags(y, sr, energy=energy_val)
        
        # 【V33.2 Full Power】提取高维 Sonic DNA (基因解剖)
        if HAS_MASTERING_CORE and MASTERING_ANALYZER and file_path:
            try:
                res["sonic_dna"] = MASTERING_ANALYZER.extract_sonic_dna(file_path)
            except Exception:
                res["sonic_dna"] = {}
        
    except Exception:
        # Fallback Swing Detection
        if len(beat_times) >= 8:
            intervals = np.diff(beat_times)
            even_intervals = intervals[0::2]
            odd_intervals = intervals[1::2]
            if len(even_intervals) > 0 and len(odd_intervals) > 0:
                min_len = min(len(even_intervals), len(odd_intervals))
                ratio = np.mean(even_intervals[:min_len] / (odd_intervals[:min_len] + 1e-6))
                res["swing_dna"] = float(np.clip(abs(ratio - 1.0), 0.0, 1.0))
            else:
                res["swing_dna"] = 0.0
        else:
            res["swing_dna"] = 0.0

    return res

def strict_bpm_check(current_bpm: float, next_bpm: float, max_diff: float = 12.0) -> bool:
    """
    严格检查BPM跨度是否在限制内
    
    Parameters:
    - current_bpm: 当前歌曲BPM
    - next_bpm: 下一首歌曲BPM
    - max_diff: 最大允许跨度（默认12）
    
    Returns:
    - True: 跨度在限制内
    - False: 跨度超过限制
    """
    if not current_bpm or not next_bpm:
        return False
    
    diff = abs(current_bpm - next_bpm)
    return diff <= max_diff

def _smart_trim_silence(y: np.ndarray, sr: int, max_silence_duration: float = 2.0) -> np.ndarray:
    """
    智能切除静音：只有在有明显静音时才切除
    
    P0优化：避免误伤正常前奏（如钢琴intro、环境音等）
    
    Args:
        y: 音频数据
        sr: 采样率
        max_silence_duration: 最大静音时长（秒）
    
    Returns:
        处理后的音频数据
    """
    try:
        # 计算RMS能量
        rms = librosa.feature.rms(y=y)[0]
        rms_times = librosa.frames_to_time(range(len(rms)), sr=sr)
        
        # 检查前max_silence_duration秒是否完全无声
        silence_threshold = 0.01  # 非常低的阈值
        silence_start = None
        
        for i, t in enumerate(rms_times):
            if t > max_silence_duration:
                break
            if rms[i] < silence_threshold:
                if silence_start is None:
                    silence_start = t
            else:
                # 有声音，重置静音起点
                silence_start = None
        
        # 如果有明显静音（至少0.5秒），切除
        if silence_start is not None and silence_start > 0.5:
            y_trimmed, _ = librosa.effects.trim(y, top_db=40)
            return y_trimmed
        
        return y  # 没有明显静音，保留原样
    except Exception:
        # 如果检测失败，保留原样
        return y


def _detect_downbeat_by_periodicity(beat_times: List[float], beat_energies: List[float], 
                                    beats_per_bar: int = 4) -> float:
    """
    通过周期性模式检测强拍（改进版）
    
    P0优化：检测周期性模式，而不是只找能量最强的beat
    
    原理：每beats_per_bar个beat应该有一个强拍
    找到周期性最强的offset
    
    Args:
        beat_times: beat时间点列表
        beat_energies: beat能量列表
        beats_per_bar: 每小节拍数（4/4拍=4，3/4拍=3）
    
    Returns:
        强拍时间点
    """
    if len(beat_energies) < beats_per_bar * 2:
        return beat_times[0] if beat_times else 0.0  # 数据不足，使用第一个beat
    
    best_offset = 0
    best_score = -1
    
    # 尝试不同的offset（0到beats_per_bar-1）
    for offset in range(beats_per_bar):
        # 提取每beats_per_bar个beat中的第一个（强拍）
        downbeat_energies = [beat_energies[i] for i in range(offset, len(beat_energies), beats_per_bar)]
        # 提取其他beat（弱拍）
        weakbeat_energies = [beat_energies[i] for i in range(len(beat_energies)) if i % beats_per_bar != offset]
        
        if len(downbeat_energies) >= 2 and len(weakbeat_energies) >= 2:
            # 计算强拍和弱拍的能量差异
            downbeat_avg = np.mean(downbeat_energies)
            weakbeat_avg = np.mean(weakbeat_energies)
            
            if weakbeat_avg > 0:
                # 周期性得分 = 强拍/弱拍比例 + 强拍稳定性
                periodicity_score = (downbeat_avg / weakbeat_avg) * (1.0 - np.std(downbeat_energies) / (downbeat_avg + 1e-6))
                
                if periodicity_score > best_score:
                    best_score = periodicity_score
                    best_offset = offset
    
    # 返回对应offset的beat时间
    if best_offset < len(beat_times):
        return beat_times[best_offset]
    return beat_times[0] if beat_times else 0.0


def deep_analyze_track(file_path: str, db_bpm: Optional[float] = None, detect_drop: bool = False, existing_analysis: Optional[Dict] = None) -> Optional[Dict]:
    """
    使用librosa深度分析单首歌曲
    分析BPM、能量、结构等
    
    Parameters:
    - file_path: 音频文件路径
    - db_bpm: 数据库中的BPM（用于验证和修正）
    - detect_drop: 是否检测Drop位置（默认False，不检测）
    - existing_analysis: 如果提供，则尝试增量更新缺失维度（如 v1.2 的新维度），跳过重型计算
    """
    if not HAS_LIBROSA or not os.path.exists(file_path):
        return None

    # 如果已有完整分析，且包含关键新维度，直接返回
    if existing_analysis and "language" in existing_analysis and "kick_hardness" in existing_analysis and "true_start_sec" in existing_analysis:
        return existing_analysis

    try:
        # 检查文件大小，如果超过500MB，限制分析时长
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        max_duration = None
        if file_size_mb > 500:
            max_duration = 600
        elif file_size_mb > 200:
            max_duration = 300
        
        # 加载音频文件
        y, sr = librosa.load(file_path, sr=22050, duration=max_duration)
        
        # 如果是增量更新（已有基础分析，只需补全轻量维度）
        if existing_analysis and "bpm" in existing_analysis:
            res = existing_analysis.copy()
            bpm = res.get("bpm", 120.0)
            # 简单估算 beat_times（用于轻量分析）
            duration = len(y) / sr
            beat_times = np.arange(0, duration, 60.0 / max(1.0, bpm))
            
            # 补重新维度
            extra = analyze_mix_metrics_light(y=y, sr=sr, bpm=bpm, beat_times=beat_times, file_path=file_path)
            if extra:
                res.update(extra)
            return res

        # 以下是完整的重型分析流程...
        # 切除静音
        if y.size > 0:
            y, _ = librosa.effects.trim(y, top_db=40)
        
        # BPM检测（基于节拍跟踪，使用完整音频）
        # 设置合理的BPM范围：60-200 BPM
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=120)
        bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        beat_times = librosa.frames_to_time(beats, sr=sr)  # 提前计算beat_times供后续使用
        
        # ========== 拍号检测（Time Signature Detection） ==========
        # 检测4/4、3/4、6/8等拍号
        time_signature = "4/4"  # 默认4/4拍
        time_signature_confidence = 0.5  # 默认中等置信度
        
        if len(beat_times) >= 12:  # 至少需要12个beat才能检测拍号
            try:
                # 分析节拍强度模式
                rms = librosa.feature.rms(y=y)[0]
                rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
                
                # 计算每个beat附近的能量强度
                beat_energies = []
                for beat_time in beat_times[:min(32, len(beat_times))]:  # 分析前32个beat
                    beat_idx = np.argmin(np.abs(rms_times - beat_time))
                    if beat_idx < len(rms):
                        window_start = max(0, beat_idx - int(0.1 * sr / 512))
                        window_end = min(len(rms), beat_idx + int(0.1 * sr / 512))
                        if window_end > window_start:
                            beat_energy = np.mean(rms[window_start:window_end])
                            beat_energies.append(beat_energy)
                
                if len(beat_energies) >= 12:
                    # 检测4/4拍模式（强-弱-中-弱）
                    # 每4个beat应该有一个强拍（downbeat）
                    pattern_4_4_scores = []
                    for offset in range(4):  # 尝试4种可能的强拍位置
                        # 提取每4个beat中的第一个（强拍）
                        downbeats = [beat_energies[i] for i in range(offset, len(beat_energies), 4)]
                        # 提取每4个beat中的其他拍（弱拍）
                        weak_beats = [beat_energies[i] for i in range(len(beat_energies)) if i % 4 != offset]
                        
                        if len(downbeats) >= 2 and len(weak_beats) >= 2:
                            # 计算强拍和弱拍的能量差异
                            downbeat_avg = np.mean(downbeats)
                            weakbeat_avg = np.mean(weak_beats)
                            if weakbeat_avg > 0:
                                pattern_score = downbeat_avg / weakbeat_avg  # 强拍/弱拍比例
                                pattern_4_4_scores.append((offset, pattern_score))
                    
                    # 检测3/4拍模式（强-弱-弱）
                    pattern_3_4_scores = []
                    for offset in range(3):  # 尝试3种可能的强拍位置
                        downbeats = [beat_energies[i] for i in range(offset, len(beat_energies), 3)]
                        weak_beats = [beat_energies[i] for i in range(len(beat_energies)) if i % 3 != offset]
                        
                        if len(downbeats) >= 2 and len(weak_beats) >= 2:
                            downbeat_avg = np.mean(downbeats)
                            weakbeat_avg = np.mean(weak_beats)
                            if weakbeat_avg > 0:
                                pattern_score = downbeat_avg / weakbeat_avg
                                pattern_3_4_scores.append((offset, pattern_score))
                    
                    # 选择最佳匹配
                    if pattern_4_4_scores:
                        best_4_4 = max(pattern_4_4_scores, key=lambda x: x[1])
                        best_4_4_score = best_4_4[1]
                    else:
                        best_4_4_score = 1.0
                    
                    if pattern_3_4_scores:
                        best_3_4 = max(pattern_3_4_scores, key=lambda x: x[1])
                        best_3_4_score = best_3_4[1]
                    else:
                        best_3_4_score = 1.0
                    
                    # 判断拍号（需要明显的模式差异）
                    if best_3_4_score > best_4_4_score * 1.2 and best_3_4_score > 1.15:
                        # 3/4拍模式更明显
                        time_signature = "3/4"
                        time_signature_confidence = min(0.9, best_3_4_score / 2.0)
                    elif best_4_4_score > 1.1:
                        # 4/4拍模式明显
                        time_signature = "4/4"
                        time_signature_confidence = min(0.9, best_4_4_score / 2.0)
                    else:
                        # 模式不明显，默认4/4拍
                        time_signature = "4/4"
                        time_signature_confidence = 0.5
            except Exception as e:
                # 检测失败，使用默认值
                time_signature = "4/4"
                time_signature_confidence = 0.5
        
        # ========== P0-1优化：下拍检测Ensemble（多模型+投票机制）==========
        # 强拍对齐检测（Downbeat Alignment）
        # 检测第一个强拍的位置（相对于歌曲开始的时间）
        # 根据检测到的拍号调整强拍检测逻辑
        downbeat_offset = 0.0  # 默认第一个beat就是强拍
        beats_per_bar = 4 if time_signature == "4/4" else (3 if time_signature == "3/4" else 4)
        downbeat_confidence = 0.5  # 默认中等置信度
        needs_manual_alignment = False
        beatgrid_fix_hint = None
        ensemble_metadata = {}
        
        if len(beat_times) > 0:
            # P0-1优化：优先使用Ensemble检测
            try:
                from downbeat_ensemble_detector import detect_downbeat_ensemble
                
                # 尝试使用64拍窗口，fallback到32拍
                for window_size in [64, 32]:
                    ensemble_result, ensemble_conf, ensemble_meta = detect_downbeat_ensemble(
                        y=y, sr=sr, beat_times=beat_times, 
                        beats_per_bar=beats_per_bar,
                        analysis_window_beats=window_size
                    )
                    
                    if ensemble_result is not None and ensemble_conf >= 0.4:
                        # Ensemble检测成功
                        downbeat_offset = ensemble_result
                        downbeat_confidence = ensemble_conf
                        ensemble_metadata = ensemble_meta
                        needs_manual_alignment = ensemble_conf < 0.6
                        
                        # 计算beatgrid_fix_hint
                        from beatgrid_fix_helper import calculate_beatgrid_fix_hint
                        downbeat_offset_in_beats = (downbeat_offset * bpm / 60.0) if bpm > 0 else 0
                        fix_hint = calculate_beatgrid_fix_hint(
                            downbeat_offset_in_beats, beats_per_bar, bpm
                        )
                        beatgrid_fix_hint = fix_hint["hint_text"]
                        if fix_hint["needs_manual_alignment"]:
                            needs_manual_alignment = True
                        break
            except ImportError:
                # 如果模块不存在，使用原有方法
                pass
            except Exception as e:
                # Ensemble检测失败，fallback到原有方法
                pass
            
            # Fallback：如果Ensemble检测失败，使用原有方法
            if downbeat_offset == 0.0 or (ensemble_metadata and not ensemble_metadata.get("ensemble_result")):
                first_beat = float(beat_times[0])
                
                # ========== 【修复1B】算法修复：强拍检测窗口扩大（32拍，更稳定） ==========
                if len(beat_times) >= 32:
                    beat_duration = 60.0 / bpm if bpm > 0 else 0.5
                    analysis_window = min(32 * beat_duration, 20.0)
                    
                    analysis_beats = [bt for bt in beat_times if bt <= analysis_window]
                    
                    if len(analysis_beats) >= beats_per_bar * 2:
                        rms = librosa.feature.rms(y=y)[0]
                        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
                        
                        beat_energies_list = []
                        beat_times_list = []
                        for beat_time in analysis_beats[:32]:
                            beat_idx = np.argmin(np.abs(rms_times - beat_time))
                            if beat_idx < len(rms):
                                window_start = max(0, beat_idx - int(0.1 * sr / 512))
                                window_end = min(len(rms), beat_idx + int(0.1 * sr / 512))
                                if window_end > window_start:
                                    beat_energy = np.mean(rms[window_start:window_end])
                                    beat_energies_list.append(beat_energy)
                                    beat_times_list.append(beat_time)
                        
                        if len(beat_energies_list) >= beats_per_bar * 2:
                            downbeat_offset = _detect_downbeat_by_periodicity(beat_times_list, beat_energies_list, beats_per_bar)
                        else:
                            downbeat_offset = first_beat
                    else:
                        downbeat_offset = first_beat
                else:
                    downbeat_offset = first_beat
                
                # ========== 【修复1C】Fallback 改进：downbeat_offset==0 时触发次级检测 ==========
                if downbeat_offset == 0.0 or downbeat_offset is None:
                    try:
                        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                        if len(onset_env) > 0 and len(beat_times) >= 8:
                            beat_energies = []
                            for bt in beat_times[:8]:
                                beat_idx = int(bt * sr / 512) if sr > 0 else 0
                                if 0 <= beat_idx < len(onset_env):
                                    beat_energies.append((bt, float(onset_env[beat_idx])))
                            
                            if beat_energies:
                                strongest_beat = max(beat_energies, key=lambda x: x[1])
                                if strongest_beat[1] > np.mean([e[1] for e in beat_energies]) * 1.2:
                                    downbeat_offset = strongest_beat[0]
                    except Exception:
                        pass
        
        # ========== P0 优化：迭代式 BPM Octave 纠偏与多源修正 ==========
        # 1. 初始修正：尝试使用 librosa.feature.tempo 作为辅助参考
        try:
            # 这里的 tempo 计算通常比 beat_track 稳定（但只是浮点数）
            global_tempo_res = librosa.feature.tempo(y=y, sr=sr, start_bpm=120)
            global_tempo = float(global_tempo_res[0])
            
            # 如果 beat_track 的结果与全局 tempo 处于不同的 octave，进行初步对齐
            if global_tempo > 0:
                while bpm < global_tempo * 0.7:
                    bpm *= 2
                while bpm > global_tempo * 1.4:
                    bpm /= 2
        except Exception:
            pass

        # 2. 数据库 BPM 绝对优先策略 (Rekordbox Priority)
        if db_bpm and db_bpm > 0:
            # 强制对齐到数据库值，禁止 AI 深度分析覆盖手动校准结果
            if abs(bpm - db_bpm) > 0.01:
                print(f"  [BPM锁定] 优先使用数据库值: {bpm:.1f} -> {db_bpm:.1f}")
                bpm = db_bpm
        else:
            # 3. 流行/电子乐合理区间强制纠偏 (Octave Cycle)
            # 从外部配置加载阈值
            try:
                config_path = r"d:\anti\config\dj_rules.yaml"
                with open(config_path, 'r', encoding='utf-8') as f:
                    dj_config = yaml.safe_load(f)
                limit_min = float(dj_config.get('bpm_range_min', 65.0))
                limit_max = float(dj_config.get('bpm_range_max', 195.0))
            except Exception:
                # Fallback to safe defaults if config fails
                limit_min = 65.0
                limit_max = 190.0
            
            # 循环倍增/减半，确保曲目不会因为 1/4 或 4 倍速陷阱导致极端数值
            loop_count = 0
            while bpm < limit_min and loop_count < 3:
                bpm *= 2
                loop_count += 1
                print(f"  [BPM纠偏] 低于下限 {limit_min}，尝试倍增: {bpm/2:.1f} -> {bpm:.1f}")
                
            loop_count = 0
            while bpm > limit_max and loop_count < 3:
                bpm /= 2
                loop_count += 1
                print(f"  [BPM纠偏] 高于上限 {limit_max}，尝试减半: {bpm*2:.1f} -> {bpm:.1f}")

        # 最终安全检查
        bpm = float(np.clip(bpm, 40.0, 280.0))
        
        # 计算beat_stability（拍点稳定性）和bpm_confidence（BPM可信度）
        beat_stability = 0.5  # 默认中等稳定性
        bpm_confidence = 0.5  # 默认中等可信度
        
        try:
            if len(beat_times) >= 4:
                # 计算节拍间隔
                beat_intervals = []
                for i in range(1, len(beat_times)):
                    interval = beat_times[i] - beat_times[i-1]
                    beat_intervals.append(interval)
                
                if len(beat_intervals) >= 2:
                    interval_mean = float(np.mean(beat_intervals))
                    interval_std = float(np.std(beat_intervals))
                    
                    # beat_stability = 1 - (标准差 / 平均值)，规律性越强，稳定性越高
                    if interval_mean > 0:
                        beat_stability = max(0.0, min(1.0, 1.0 - (interval_std / interval_mean)))
                    else:
                        beat_stability = 0.5
                    
                    # 计算预期间隔（基于BPM）
                    expected_interval = 60.0 / bpm if bpm > 0 else 0.5
                    # 如果实际间隔与预期间隔接近，说明BPM检测准确
                    interval_match = 1.0 - min(1.0, abs(interval_mean - expected_interval) / expected_interval)
                    
                    # bpm_confidence = beat_stability * interval_match
                    bpm_confidence = beat_stability * interval_match
                    
                    # 如果有数据库BPM，与数据库BPM对比
                    if db_bpm and db_bpm > 0:
                        # 如果检测到的BPM与数据库BPM接近，提升可信度
                        bpm_match_ratio = 1.0 - min(1.0, abs(bpm - db_bpm) / max(db_bpm, bpm))
                        # 取beat_stability和bpm_match_ratio的较大值，但不超过1.0
                        bpm_confidence = max(bpm_confidence, min(0.95, beat_stability * 0.8 + bpm_match_ratio * 0.2))
                    else:
                        # 没有数据库BPM时，仅基于beat_stability
                        bpm_confidence = beat_stability
                else:
                    # 节拍太少，稳定性低
                    beat_stability = 0.3
                    bpm_confidence = 0.3
            else:
                # 节拍太少，稳定性低
                beat_stability = 0.3
                bpm_confidence = 0.3
        except Exception:
            beat_stability = 0.5
            bpm_confidence = 0.5
        
        # 能量分析（改为分段RMS + 鼓点密度，突出慢歌/快歌差异）
        try:
            frame_length = 2048
            hop_length = 512
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)

            rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
            rms_global = float(np.mean(rms_norm))

            thirds = np.array_split(rms_norm, 3)
            thirds_mean = [float(np.mean(part)) for part in thirds]
            energy_var = float(np.var(thirds_mean))

            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
            onset_norm = (onset_env - np.min(onset_env)) / (np.max(onset_env) - np.min(onset_env) + 1e-6)
            onset_global = float(np.mean(onset_norm))
            onset_std = float(np.std(onset_norm))  # 计算onset方差（用于律动相似度，更稳定）

            D = librosa.stft(y)
            D_harm, D_perc = librosa.decompose.hpss(D)
            perc_power = np.sum(np.abs(D_perc))
            total_power = np.sum(np.abs(D)) + 1e-6
            perc_ratio = float(perc_power / total_power)
            
            # MFCC特征提取（用于音色连续性）
            # 提取13个MFCC系数（标准配置）
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            # 计算MFCC均值（代表整体音色特征）
            mfcc_mean = np.mean(mfcc, axis=1).tolist()  # 13维向量

            # 节奏紧凑度（Groove Density）计算
            # 基于鼓击间隔的规律性（节奏紧凑度）
            # 用于区分"节奏紧凑度"和"能量强度"，避免Tech House / Afrobeat被误判为高能量
            groove_density = 0.5  # 默认中等紧凑度
            if len(beat_times) >= 4:
                # 计算节拍间隔
                beat_intervals = []
                for i in range(1, len(beat_times)):
                    interval = beat_times[i] - beat_times[i-1]
                    beat_intervals.append(interval)
                
                if len(beat_intervals) >= 2:
                    interval_mean = float(np.mean(beat_intervals))
                    interval_std = float(np.std(beat_intervals))
                    
                    # 规律性 = 1 - (标准差 / 平均值)
                    # 规律性越强，节奏紧凑度越高
                    if interval_mean > 0:
                        regularity = 1.0 - min(1.0, interval_std / interval_mean)
                    else:
                        regularity = 0.5
                    
                    # 计算onset密度（每秒onset数）
                    # 使用onset_global（已经归一化的onset强度）来估算onset密度
                    # onset_global是归一化的onset强度均值，乘以5作为onset密度的近似（经验值）
                    total_duration = len(y) / sr
                    onset_density = onset_global * 5.0 if 'onset_global' in locals() else 2.0
                    
                    # 节奏紧凑度 = 规律性 * onset密度（归一化）
                    # 规律性强 + onset密度高 = 节奏紧凑度高
                    groove_density = regularity * min(1.0, onset_density / 5.0)  # 归一化到0-1
                    groove_density = float(groove_density)
            
            # 能量计算：加入BPM因子，让快歌能量值更高
            # BPM因子：以120 BPM为基准，每增加/减少10 BPM，能量增加/减少5%
            bpm_factor = (bpm - 120) / 120.0  # 归一化BPM差异（120为基准）
            bpm_energy_boost = max(-0.15, min(0.25, bpm_factor * 0.5))  # 限制在-15%到+25%之间
            
            # 基础能量（RMS + Onset + Percussive）
            # 节奏紧凑度修正：如果节奏紧凑度高但RMS能量低，可能是Tech House / Afrobeat
            # 这种情况下，降低onset密度对能量的影响，避免误判
            if groove_density > 0.7 and rms_global < 0.3:
                # 节奏紧凑但能量不高，降低onset权重（从0.3降低到0.15）
                adjusted_onset_weight = 0.15
            else:
                adjusted_onset_weight = 0.3
            
            base_energy_score = 0.45 * rms_global + adjusted_onset_weight * onset_global + 0.2 * perc_ratio
            # 加入BPM因子（25%权重），让快歌能量更高
            energy_score = base_energy_score * (1.0 + bpm_energy_boost * 0.25)
            
            # 如果节奏紧凑度高但RMS能量低，进一步降低能量值（避免误判）
            if groove_density > 0.7 and rms_global < 0.3:
                energy_score *= 0.85  # 降低15%能量值，避免Tech House / Afrobeat被误判为高能量
            
            energy_level = int(min(100, max(0, energy_score * 100)))

            energy_profile = {
                'overall': energy_level,
                'rms_global': rms_global,
                'rms_segments': thirds_mean,
                'energy_variance': energy_var,
                'onset_global': onset_global,
                'onset_std': onset_std,  # onset方差（用于律动相似度，更稳定）
                'percussive_ratio': perc_ratio,
                'mfcc_mean': mfcc_mean,  # MFCC均值（用于音色连续性）
                'groove_density': groove_density,  # 节奏紧凑度（用于能量修正，避免Tech House / Afrobeat误判）
            }
        except Exception:
            energy_level = 50
            energy_profile = None
        
        # 确保能量在合理范围内（20-100），避免过低
        energy_level = max(20, min(100, energy_level))
        
        # 动态范围分析（用于评估能量变化）
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # 计算onset频率（Hz）用于风格标签和鼓型/律动分析
        total_duration = len(y) / sr
        onset_count = len(onset_frames)
        onset_frequency = onset_count / total_duration if total_duration > 0 else 0.0
        
        # ========== 风格检测优化：文件名 + 音频特征结合 ==========
        # 1. 先尝试从文件名检测（华语/K-Pop等亚洲歌曲更准确）
        genre_tag = None
        genre = None
        try:
            from genre_compatibility import detect_genre_from_filename, detect_chinese_subgenre, has_chinese_characters
            filename = os.path.basename(file_path)
            
            # 检测华语歌曲
            if has_chinese_characters(filename):
                genre = detect_chinese_subgenre(filename)
                if genre and genre.startswith('chinese_'):
                    # 华语歌曲使用专门的genre_tag
                    if genre in ['chinese_hiphop']:
                        genre_tag = "Hip-Hop/华语"
                    elif genre in ['chinese_dance']:
                        genre_tag = "Dance/华语"
                    elif genre in ['chinese_ballad', 'chinese_folk']:
                        genre_tag = "Ballad/华语"
                    elif genre in ['chinese_rock']:
                        genre_tag = "Rock/华语"
                    elif genre in ['chinese_traditional']:
                        genre_tag = "Traditional/华语"
                    else:
                        genre_tag = "Pop/华语"
            
            # 如果文件名没检测到，尝试通用检测
            if not genre_tag:
                detected = detect_genre_from_filename(filename)
                if detected and detected not in ['electronic', 'house']:
                    genre = detected
                    if detected in ['kpop', 'jpop']:
                        genre_tag = f"Pop/{detected.upper()}"
                    elif detected in ['hip_hop', 'trap']:
                        genre_tag = "Hip-Hop"
                    elif detected in ['pop', 'dance_pop']:
                        genre_tag = "Pop"
        except Exception:
            pass
        
        # 2. 如果文件名没检测到，使用音频特征（适合电子乐）
        if not genre_tag:
            if bpm < 110 and onset_frequency < 4.0:
                genre_tag = "Deep/Chill"
            elif bpm >= 160 or (bpm >= 140 and onset_frequency > 6.0):
                genre_tag = "DnB/Hard"
            elif 110 <= bpm <= 140 and onset_frequency <= 6.0:
                genre_tag = "House/Tech"
            elif onset_frequency < 4.0:
                genre_tag = "Deep/Chill"
            elif onset_frequency > 7.0:
                genre_tag = "DnB/Hard"
            else:
                genre_tag = "House/Tech"
        
        # 节拍强度
        beat_strength = np.mean(librosa.beat.beat_track(y=y, sr=sr)[1])

        # ========== 新增增强模块：人声 / 鼓型 / 乐句长度基础特征 ==========
        # 这些特征仅用于排序时的“软规则”，不会作为硬过滤条件
        # 1) 人声占比（vocal_presence）和人声时间片段（vocal_segments）
        vocal_presence = 0.0
        vocal_segments_list = []
        try:
            # deep_analyze_track 内前面的人声检测已经给出 vocals_detection / vocal_ratio
            if 'vocal_ratio' in locals():
                vocal_presence = float(vocal_ratio)
            if isinstance(vocals_detection, dict):
                segs = vocals_detection.get('segments') or []
                # 确保为 (start, end) 的简单列表，便于排序模块使用
                vocal_segments_list = [
                    (float(s), float(e)) for (s, e) in segs if e > s
                ]
        except Exception:
            vocal_presence = 0.0
            vocal_segments_list = []

        # 2) 鼓型 / 律动（drum_pattern & groove_density）- 【优化A】增强分类
        drum_pattern = "unknown"
        drum_group = "other"
        groove_density_value = None
        snare_peak_at_3rd_beat_ratio = 0.0
        four_on_floor_kick_ratio = 0.0
        try:
            if isinstance(energy_profile, dict):
                gd = energy_profile.get('groove_density')
                if gd is not None:
                    groove_density_value = float(gd)
            if groove_density_value is None:
                groove_density_value = 0.5

            # 【优化A】检测 snare/kick 模式（用于更准确的分类）
            if 'beat_times' in locals() and len(beat_times) >= 16 and 'onset_times' in locals():
                try:
                    # 使用 HPSS 分离打击乐
                    y_harm, y_perc = librosa.effects.hpss(y=y)
                    # 计算每拍的打击乐能量
                    beat_energies = []
                    for bt in beat_times[:min(64, len(beat_times))]:
                        # 找到该拍附近的 onset
                        nearby_onsets = [ot for ot in onset_times if abs(ot - bt) < 0.2]
                        if nearby_onsets:
                            beat_energies.append(len(nearby_onsets))
                        else:
                            beat_energies.append(0)
                    
                    if len(beat_energies) >= 16:
                        # 检测 snare 在第3拍的模式（Trap特征）
                        # 每4拍为一组，检查第3拍是否有峰值
                        snare_3rd_count = 0
                        total_groups = 0
                        for i in range(0, len(beat_energies) - 4, 4):
                            group = beat_energies[i:i+4]
                            if len(group) == 4:
                                total_groups += 1
                                # 第3拍（索引2）能量最高或次高
                                if group[2] >= max(group[0], group[1], group[3]) * 0.8:
                                    snare_3rd_count += 1
                        if total_groups > 0:
                            snare_peak_at_3rd_beat_ratio = snare_3rd_count / total_groups
                        
                        # 检测 four_on_floor kick 模式（每拍都有kick）
                        four_on_floor_count = 0
                        for i in range(0, len(beat_energies) - 4, 4):
                            group = beat_energies[i:i+4]
                            if len(group) == 4:
                                # 每拍都有能量（four_on_floor）
                                if all(e > 0 for e in group):
                                    four_on_floor_count += 1
                        if total_groups > 0:
                            four_on_floor_kick_ratio = four_on_floor_count / total_groups
                except Exception:
                    # 检测失败不影响主流程
                    pass

            # 【优化A】增强的鼓型分类（按优先级顺序）
            # P1-3优化：进一步细分鼓型
            ts = time_signature or "4/4"
            bp = bpm

            # P1-3优化：先检测特殊细分类型
            drum_pattern_subtype = None  # 新增：鼓型子类型
            
            # 1. Trap（最高优先级：60-80 或 130-160 BPM，snare在第3拍显著）
            # ========== 【修复8】Trap 判定：snare 在第3拍显著 ==========
            if (60 <= bp <= 80 or 130 <= bp <= 160) and snare_peak_at_3rd_beat_ratio >= 0.6:
                # 提高阈值从 0.35 到 0.6，更准确识别 Trap
                drum_pattern = "trap"
                drum_group = "broken"
                # P1-3优化：细分Trap类型
                if 60 <= bp <= 80:
                    drum_pattern_subtype = "trap_half_time"
                elif 130 <= bp <= 145:
                    drum_pattern_subtype = "trap_normal"
                else:
                    drum_pattern_subtype = "trap_fast"
            # 2. Reggaeton / Dembow（92-110 BPM，不规则kick-snare）
            elif 92 <= bp <= 110 and 0.45 <= groove_density_value <= 0.75:
                drum_pattern = "reggaeton"
                drum_group = "latin"
                # P1-3优化：细分Latin类型
                if 92 <= bp <= 98:
                    drum_pattern_subtype = "reggaeton_slow"
                elif 98 <= bp <= 105:
                    drum_pattern_subtype = "dembow"
                else:
                    drum_pattern_subtype = "reggaeton_fast"
            # 3. Hardstyle / Hard Dance（140-165 BPM，four_on_floor kick + kick_hardness 高）
            # ========== 【修复8】鼓型分类优化：防止 Trap / Hardstyle 混淆 ==========
            # 优先检测 Hardstyle（高 BPM + 强四拍kick + kick_hardness 高）
            # 注意：kick_hardness 在后面计算，这里先检查 four_on_floor_kick_ratio
            # P1-3优化：修复逻辑，使用elif而不是if
            elif 140 <= bp <= 165 and four_on_floor_kick_ratio >= 0.8 and not ((60 <= bp <= 80 or 130 <= bp <= 160) and snare_peak_at_3rd_beat_ratio >= 0.6):
                # 先标记为 hardstyle 候选，后续如果有 kick_hardness 会进一步确认
                drum_pattern = "hardstyle"
                drum_group = "4x4"
                # P1-3优化：细分Hardstyle类型
                if 140 <= bp <= 150:
                    drum_pattern_subtype = "hardstyle_classic"
                elif 150 <= bp <= 160:
                    drum_pattern_subtype = "hardstyle_raw"
                else:
                    drum_pattern_subtype = "hardstyle_extreme"
            # 4. Four-on-Floor（标准House/EDM）
            elif four_on_floor_kick_ratio >= 0.7 or (ts.startswith("4/4") and groove_density_value >= 0.55 and 118 <= bp <= 140):
                drum_pattern = "four_on_floor"
                drum_group = "4x4"
                # P1-3优化：细分Four-on-Floor类型
                if 118 <= bp <= 125:
                    if groove_density_value < 0.5:
                        drum_pattern_subtype = "deep_house"
                    else:
                        drum_pattern_subtype = "progressive_house"
                elif 125 <= bp <= 130:
                    if groove_density_value >= 0.65:
                        drum_pattern_subtype = "tech_house"
                    else:
                        drum_pattern_subtype = "house"
                elif 130 <= bp <= 140:
                    drum_pattern_subtype = "edm"
                else:
                    drum_pattern_subtype = "house"
            # 5. Shuffle / Garage（中速 + swing）
            elif 110 <= bp <= 130 and 0.45 <= groove_density_value <= 0.7:
                drum_pattern = "shuffle"
                drum_group = "4x4"
                # P1-3优化：细分Shuffle类型
                if groove_swing and groove_swing > 0.3:
                    if 110 <= bp <= 120:
                        drum_pattern_subtype = "uk_garage"
                    else:
                        drum_pattern_subtype = "future_garage"
                else:
                    drum_pattern_subtype = "shuffle"
            # 6. Breakbeat / DnB（高BPM + 不规则）
            elif bp >= 160 and groove_density_value >= 0.4:
                drum_pattern = "breakbeat"
                drum_group = "broken"
                # P1-3优化：细分Breakbeat类型
                if 160 <= bp <= 175:
                    drum_pattern_subtype = "drum_and_bass"
                elif 175 <= bp <= 185:
                    drum_pattern_subtype = "jungle"
                else:
                    drum_pattern_subtype = "hardcore"
            # 7. 默认
            else:
                drum_pattern = "breakbeat"
                drum_group = "other"
                drum_pattern_subtype = "unknown"
        except Exception:
            drum_pattern = "unknown"
            drum_group = "other"
            groove_density_value = groove_density_value if groove_density_value is not None else 0.5

        # 3) 乐句长度估计（phrase_length / phrase_confidence）
        # P1-1优化：使用多尺度乐句边界检测
        phrase_length_beats = 32
        phrase_confidence = 0.5
        phrase_boundaries = []
        try:
            # P1-1优化：使用多尺度检测器（如果可用）
            try:
                from phrase_boundary_detector import detect_phrase_boundaries_multi_scale
                if 'beat_times' in locals() and len(beat_times) >= 32:
                    multi_scale_result = detect_phrase_boundaries_multi_scale(
                        y=y, sr=sr, bpm=bpm, beat_times=beat_times
                    )
                    phrase_length_beats = multi_scale_result.get('phrase_length_dominant', 32)
                    phrase_confidence = multi_scale_result.get('phrase_confidence', 0.5)
                    phrase_boundaries = multi_scale_result.get('phrase_boundaries', [])
            except ImportError:
                # 如果模块不存在，回退到原有方法
                if 'beat_times' in locals() and len(beat_times) >= 32:
                    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                    onset_times_all = librosa.frames_to_time(
                        np.arange(len(onset_env)), sr=sr
                    )

                    beat_energies = []
                    for bt in beat_times:
                        idx = int(np.argmin(np.abs(onset_times_all - bt)))
                        if 0 <= idx < len(onset_env):
                            beat_energies.append(float(onset_env[idx]))

                    if len(beat_energies) >= 32:
                        be = np.array(beat_energies, dtype=np.float32)
                        be = be - np.mean(be)
                        std = np.std(be)
                        if std > 1e-6:
                            be = be / std

                        candidate_lags = [16, 32, 48, 64]
                        best_corr = -1.0
                        best_lag = 32

                        for lag in candidate_lags:
                            if len(be) > lag + 4:
                                a = be[:-lag]
                                b = be[lag:]
                                denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6)
                                if denom <= 0:
                                    continue
                                corr = float(np.dot(a, b) / denom)
                                if corr > best_corr:
                                    best_corr = corr
                                    best_lag = lag

                        phrase_length_beats = int(best_lag)
                        # 将相关系数映射到 0-1 置信度区间
                        phrase_confidence = float(max(0.0, min(1.0, (best_corr + 1.0) / 2.0)))
            except Exception:
                phrase_length_beats = 32
                phrase_confidence = 0.5
                phrase_boundaries = []
        except Exception:
            phrase_length_beats = 32
            phrase_confidence = 0.5
            phrase_boundaries = []
        
        # 混音点检测（Mix-In和Mix-Out点）- 基于DJ知识重新设计
        # DJ混音通常基于4个八拍（32拍）或8个八拍（64拍）的倍数
        mix_in_point = None
        mix_out_point = None
        try:
            total_duration = len(y) / sr
            
            # 计算节拍时长（秒/拍）
            beat_duration = 60.0 / bpm if bpm > 0 else 0.5
            
            # 计算常见的混音点时间（基于拍数）
            # 4个八拍 = 32拍，8个八拍 = 64拍，16个八拍 = 128拍
            bars_4_time = 32 * beat_duration   # 4个八拍的时间
            bars_8_time = 64 * beat_duration   # 8个八拍的时间
            bars_16_time = 128 * beat_duration  # 16个八拍的时间
            
            # 检测Intro结束点（Mix-In点）
            # DJ通常在第4个八拍（32拍）或第8个八拍（64拍）开始混入
            # 检测范围：16拍到128拍（取决于BPM，大约8-60秒）
            min_intro_time = 16 * beat_duration  # 至少16拍
            max_intro_time = min(128 * beat_duration, total_duration * 0.3)  # 最多128拍或前30%
            
            # 分析前30%的能量变化，找到Intro结束点
            intro_analysis_duration = min(total_duration * 0.3, 60.0)
            intro_samples = int(intro_analysis_duration * sr)
            intro_audio = y[:intro_samples]
            
            # 使用RMS能量检测结构变化
            rms_full = librosa.feature.rms(y=y)[0]
            rms_times = librosa.frames_to_time(np.arange(len(rms_full)), sr=sr)
            
            # 计算Intro部分的平均能量
            intro_rms = librosa.feature.rms(y=intro_audio)[0]
            intro_avg_energy = np.mean(intro_rms)
            
            # 查找能量明显上升的点（通常是Intro结束，Verse/Chorus开始）
            candidate_mix_in = []
            for i in range(1, len(rms_full)):
                time = rms_times[i]
                if min_intro_time <= time <= max_intro_time:
                    # 检查能量是否明显上升（上升30%以上）
                    if rms_full[i] > intro_avg_energy * 1.3:
                        # 检查是否在节拍边界附近（优先32拍、64拍的倍数）
                        beats_from_start = int(time / beat_duration)
                        # 检查是否是8拍、16拍、32拍、64拍的倍数
                        if beats_from_start % 8 == 0:  # 对齐到8拍边界
                            candidate_mix_in.append((time, beats_from_start, abs(beats_from_start % 32)))
            
            # 优先选择32拍或64拍的倍数
            if candidate_mix_in:
                # 排序：优先32拍倍数，其次64拍倍数，然后其他8拍倍数
                candidate_mix_in.sort(key=lambda x: (
                    0 if x[1] % 32 == 0 else (1 if x[1] % 64 == 0 else 2),  # 优先32拍
                    abs(x[1] - 32),  # 接近32拍优先
                    x[0]  # 时间先后
                ))
                mix_in_point = candidate_mix_in[0][0]
            else:
                # 如果没有找到合适的点，使用32拍或64拍的位置
                if bars_4_time <= max_intro_time:
                    mix_in_point = bars_4_time  # 默认4个八拍
                elif bars_8_time <= max_intro_time:
                    mix_in_point = bars_8_time  # 或8个八拍
                else:
                    mix_in_point = min_intro_time
            
            # 对齐到最近的节拍
            if len(beat_times) > 0:
                closest_beat_idx = np.argmin(np.abs(beat_times - mix_in_point))
                mix_in_point = float(beat_times[closest_beat_idx])
            
            # 检测Outro开始点（Mix-Out点）
            # DJ通常在最后32拍或64拍开始混出
            min_outro_time = 32 * beat_duration  # 至少32拍
            max_outro_time = 128 * beat_duration  # 最多128拍
            
            outro_start_time = max(total_duration - max_outro_time, total_duration * 0.7)
            outro_end_time = total_duration - min_outro_time
            
            # 分析最后30%的能量变化
            outro_samples_start = int(outro_start_time * sr)
            outro_audio = y[outro_samples_start:]
            outro_rms = librosa.feature.rms(y=outro_audio)[0]
            outro_avg_energy = np.mean(outro_rms)
            
            # 查找能量明显下降的点（通常是最后Drop/Chorus结束，Outro开始）
            candidate_mix_out = []
            for i in range(len(rms_full) - 1, max(0, int(outro_start_time * sr / 512)), -1):
                time = rms_times[i]
                if outro_start_time <= time <= outro_end_time:
                    # 检查能量是否明显下降（下降20%以上）
                    if rms_full[i] < outro_avg_energy * 0.8:
                        # 检查是否在节拍边界附近
                        beats_from_end = int((total_duration - time) / beat_duration)
                        if beats_from_end >= 16 and beats_from_end % 8 == 0:  # 至少16拍，对齐到8拍边界
                            candidate_mix_out.append((time, beats_from_end))
            
            # 优先选择32拍或64拍的位置
            if candidate_mix_out:
                # 排序：优先接近32拍或64拍
                candidate_mix_out.sort(key=lambda x: (
                    min(abs(x[1] - 32), abs(x[1] - 64)),  # 优先32或64拍
                    x[0]  # 时间先后
                ))
                mix_out_point = candidate_mix_out[0][0]
            else:
                # 如果没有找到，使用倒数32拍或64拍的位置
                if total_duration > bars_8_time:
                    mix_out_point = total_duration - bars_8_time  # 倒数8个八拍
                elif total_duration > bars_4_time:
                    mix_out_point = total_duration - bars_4_time  # 倒数4个八拍
                else:
                    mix_out_point = max(total_duration * 0.8, total_duration - min_outro_time)
            
            # 对齐到最近的节拍
            if len(beat_times) > 0:
                closest_beat_idx = np.argmin(np.abs(beat_times - mix_out_point))
                mix_out_point = float(beat_times[closest_beat_idx])
                
        except Exception as e:
            # 如果检测失败，使用基于BPM的默认值
            try:
                beat_duration = 60.0 / bpm if bpm > 0 else 0.5
                bars_4_time = 32 * beat_duration
                bars_8_time = 64 * beat_duration
                total_duration = len(y) / sr
                
                mix_in_point = bars_4_time if bars_4_time < total_duration * 0.3 else bars_8_time
                mix_out_point = total_duration - bars_8_time if total_duration > bars_8_time else total_duration - bars_4_time
            except:
                total_duration = len(y) / sr
                mix_in_point = 15.0  # 默认15秒（大约4个八拍在128 BPM）
                mix_out_point = max(16.0, total_duration - 16.0)
        
        # 调性检测（使用chroma特征和模板匹配）
        detected_key = None
        key_confidence = 0.5  # 默认中等可信度
        try:
            # 使用chroma特征检测调性（使用CQT更准确）
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Camelot Wheel映射（Camelot编号系统）
            # 大调: C=8B, C#=3B, D=10B, D#=5B, E=12B, F=7B, F#=2B, G=9B, G#=4B, A=11B, A#=6B, B=1B
            # 小调: C=5A, C#=12A, D=7A, D#=2A, E=9A, F=4A, F#=11A, G=6A, G#=1A, A=8A, A#=3A, B=10A
            camelot_major = ['8B', '3B', '10B', '5B', '12B', '7B', '2B', '9B', '4B', '11B', '6B', '1B']
            camelot_minor = ['5A', '12A', '7A', '2A', '9A', '4A', '11A', '6A', '1A', '8A', '3A', '10A']
            
            # 大调和小调的chroma模板（基于音阶的音符分布）
            # 大调：C, D, E, F, G, A, B (0, 2, 4, 5, 7, 9, 11)
            # 小调：C, D, Eb, F, G, Ab, Bb (0, 2, 3, 5, 7, 8, 10)
            major_template = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])  # 大调音阶
            minor_template = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])  # 自然小调音阶
            
            # 归一化chroma
            chroma_norm = chroma_mean / (np.sum(chroma_mean) + 1e-6)
            
            # 计算每个调性的匹配分数
            best_score = -1
            best_key = None
            
            for i in range(12):
                # 旋转模板以匹配不同的调性
                major_rotated = np.roll(major_template, i)
                minor_rotated = np.roll(minor_template, i)
                
                # 计算匹配分数（使用点积）
                major_score = np.dot(chroma_norm, major_rotated)
                minor_score = np.dot(chroma_norm, minor_rotated)
                
                # 选择更好的匹配
                if major_score > best_score:
                    best_score = major_score
                    best_key = camelot_major[i]
                
                if minor_score > best_score:
                    best_score = minor_score
                    best_key = camelot_minor[i]
            
            # ========== 优化：增强调性检测 - 多算法融合 ==========
            # 方法1：Chroma CQT（已计算）
            chroma_score = best_score
            chroma_key = best_key
            
            # 方法2：使用Chroma STFT作为补充验证
            try:
                chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
                chroma_stft_mean = np.mean(chroma_stft, axis=1)
                chroma_stft_norm = chroma_stft_mean / (np.sum(chroma_stft_mean) + 1e-6)
                
                best_stft_score = -1
                best_stft_key = None
                for i in range(12):
                    major_rotated = np.roll(major_template, i)
                    minor_rotated = np.roll(minor_template, i)
                    major_score = np.dot(chroma_stft_norm, major_rotated)
                    minor_score = np.dot(chroma_stft_norm, minor_rotated)
                    if major_score > best_stft_score:
                        best_stft_score = major_score
                        best_stft_key = camelot_major[i]
                    if minor_score > best_stft_score:
                        best_stft_score = minor_score
                        best_stft_key = camelot_minor[i]
                
                # 如果两种方法检测结果一致，提升可信度
                if best_stft_key == chroma_key:
                    chroma_score = (chroma_score + best_stft_score) / 2.0  # 平均分数
                    key_confidence = max(0.0, min(1.0, (chroma_score - 0.3) / 0.5)) if chroma_score > 0.3 else 0.0
                    # 两种方法一致，额外提升可信度
                    key_confidence = min(1.0, key_confidence * 1.2)
                else:
                    # 两种方法不一致，降低可信度
                    key_confidence = max(0.0, min(1.0, (chroma_score - 0.3) / 0.5)) if chroma_score > 0.3 else 0.0
                    key_confidence *= 0.8  # 降低20%可信度
            except:
                # STFT方法失败，仅使用CQT方法
                key_confidence = max(0.0, min(1.0, (chroma_score - 0.3) / 0.5)) if chroma_score > 0.3 else 0.0
            
            # ========== 新增：共识检测（如果启用） ==========
            try:
                # 尝试导入配置管理器
                try:
                    from config_manager import get_config
                    config = get_config() or {}
                except ImportError:
                    config = {}
                enable_consensus = config.get('analysis.enable_consensus_detection', True)
                
                if enable_consensus:
                    from consensus_detector import consensus_key_detection, consensus_bpm_detection
                    
                    # 共识Key检测（使用已加载的音频数据，避免重复加载）
                    final_key, final_key_confidence = consensus_key_detection(
                        file_path=file_path, 
                        primary_key=chroma_key if chroma_score > 0.3 else None,
                        primary_confidence=key_confidence,
                        y=y,  # 传递已加载的音频数据
                        sr=sr  # 传递采样率
                    )
                    
                    if final_key and final_key != "未知":
                        detected_key = final_key
                        key_confidence = final_key_confidence
                        # 标记是否冲突（将在result字典中设置）
                        if final_key_confidence < 0.7:
                            key_status = 'CONFLICT'
                    else:
                        # 共识检测失败，使用原结果
                        if chroma_score > 0.3:
                            detected_key = chroma_key
                        else:
                            key_confidence = chroma_score / 0.3
                    
                    # 共识BPM检测将在BPM检测完成后调用（在result字典定义前）
            except ImportError:
                # 共识检测器未找到，使用原结果
                if chroma_score > 0.3:
                    detected_key = chroma_key
                else:
                    key_confidence = chroma_score / 0.3
            except Exception:
                # 共识检测失败，使用原结果
                if chroma_score > 0.3:
                    detected_key = chroma_key
                else:
                    key_confidence = chroma_score / 0.3
            
            # 如果匹配分数足够高，使用检测到的调性（如果共识检测未覆盖）
            if detected_key is None:
                if chroma_score > 0.3:  # 阈值可调整
                    detected_key = chroma_key
                else:
                    # 匹配分数太低，可信度降低
                    key_confidence = chroma_score / 0.3  # 归一化到 0-1
                
            # Open Key System兼容：自动转换Open Key格式到Camelot格式
            if detected_key:
                # 导入转换函数（避免循环导入）
                try:
                    from enhanced_harmonic_set_sorter import convert_open_key_to_camelot
                    detected_key = convert_open_key_to_camelot(detected_key)
                except ImportError:
                    # 如果无法导入，使用简单的转换逻辑
                    if detected_key.endswith('m'):
                        try:
                            num = int(detected_key[:-1])
                            if 1 <= num <= 12:
                                detected_key = f"{num}A"
                        except ValueError:
                            pass
                    elif detected_key.endswith('d'):
                        try:
                            num = int(detected_key[:-1])
                            if 1 <= num <= 12:
                                detected_key = f"{num}B"
                        except ValueError:
                            pass
        except Exception as e:
            detected_key = None
            key_confidence = 0.3  # 检测失败，可信度降低
        
        # ========== 优化：特定歌曲调性修正 ==========
        # Arlene MC - MamaZota: 强制使用10A (B Minor)
        file_path_lower = file_path.lower()
        if 'arlene mc' in file_path_lower and 'mamazota' in file_path_lower:
            detected_key = "10A"
            key_confidence = 0.95  # 高可信度
            # 注意：这里不打印日志，因为deep_analyze_track可能没有progress_logger
        
        # 人声和鼓点检测
        vocals_detection = None
        drums_detection = None
        try:
            total_duration = len(y) / sr
            
            # 1. 鼓点检测：使用频谱质心和高频能量
            # 鼓点通常在低频（20-200Hz）和高频（2000-8000Hz）都有能量
            # 使用频谱对比度检测打击乐特征
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            spectral_contrast_times = librosa.frames_to_time(range(spectral_contrast.shape[1]), sr=sr)
            
            # 计算每个时间点的鼓点强度（低频和高频的能量）
            # 使用onset检测配合能量分析
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=512)
            onset_times_full = librosa.frames_to_time(onset_frames, sr=sr)
            
            # 计算每个时间段的鼓点密度
            beat_density = np.zeros(len(rms_times))
            for onset_time in onset_times_full:
                idx = np.argmin(np.abs(rms_times - onset_time))
                if idx < len(beat_density):
                    beat_density[idx] += 1
            
            # 归一化鼓点密度
            if np.max(beat_density) > 0:
                beat_density_norm = beat_density / np.max(beat_density)
            else:
                beat_density_norm = np.zeros(len(rms_times))
            
            # 2. 人声检测：使用频谱质心和MFCC特征
            # 人声通常在200-3400Hz范围内，频谱质心较高
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            centroid_times = librosa.frames_to_time(range(len(spectral_centroids)), sr=sr)
            
            # 计算MFCC特征（人声有特定的MFCC模式）
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_times = librosa.frames_to_time(range(mfcc.shape[1]), sr=sr)
            
            # 人声特征：MFCC第1-3维通常较高（基频相关）
            # 计算人声强度（基于MFCC和频谱质心）
            vocals_strength = np.zeros(len(rms_times))
            for i, time in enumerate(rms_times):
                # 找到对应的MFCC和频谱质心索引
                mfcc_idx = np.argmin(np.abs(mfcc_times - time))
                centroid_idx = np.argmin(np.abs(centroid_times - time))
                
                if mfcc_idx < mfcc.shape[1] and centroid_idx < len(spectral_centroids):
                    # 人声特征：MFCC第1-3维较高，频谱质心在200-3400Hz范围
                    mfcc_vocal = np.mean(mfcc[1:4, mfcc_idx])
                    centroid_val = spectral_centroids[centroid_idx]
                    
                    # 如果频谱质心在200-3400Hz范围，且MFCC特征符合人声模式
                    if 200 <= centroid_val <= 3400:
                        vocals_strength[i] = (mfcc_vocal + 1) * (centroid_val / 2000)  # 归一化
                    else:
                        vocals_strength[i] = 0
            
            # 归一化人声强度
            if np.max(vocals_strength) > 0:
                vocals_strength_norm = vocals_strength / np.max(vocals_strength)
            else:
                vocals_strength_norm = np.zeros(len(rms_times))
            
            # 检测人声和鼓点的主要段落
            # 将歌曲分成多个时间窗口，检测每个窗口的主要特征
            window_size = 8.0  # 8秒窗口
            num_windows = int(total_duration / window_size)
            
            vocals_segments = []
            drums_segments = []
            
            for i in range(num_windows):
                start_time = i * window_size
                end_time = min((i + 1) * window_size, total_duration)
                
                # 找到对应的时间索引
                start_idx = np.argmin(np.abs(rms_times - start_time))
                end_idx = np.argmin(np.abs(rms_times - end_time))
                
                if end_idx > start_idx:
                    # 计算这个窗口的平均人声和鼓点强度
                    window_vocals = np.mean(vocals_strength_norm[start_idx:end_idx])
                    window_drums = np.mean(beat_density_norm[start_idx:end_idx])
                    
                    # 如果人声强度超过阈值，标记为人声段落
                    if window_vocals > 0.4:
                        vocals_segments.append((start_time, end_time))
                    
                    # 如果鼓点强度超过阈值，标记为鼓点段落
                    if window_drums > 0.5:
                        drums_segments.append((start_time, end_time))
            
            vocals_detection = {
                'segments': vocals_segments,
                'strength': vocals_strength_norm.tolist()[:100]  # 保存前100个值用于参考
            }
            
            drums_detection = {
                'segments': drums_segments,
                'strength': beat_density_norm.tolist()[:100]  # 保存前100个值用于参考
            }
            
            # 计算vocal_ratio（人声比例）- 基于vocals_detection
            vocal_ratio = 0.0
            if vocals_strength_norm is not None and len(vocals_strength_norm) > 0:
                # vocal_ratio = 平均人声强度（归一化到0-1）
                vocal_ratio = float(np.mean(vocals_strength_norm))
            elif vocals_segments:
                # 基于人声段落计算vocal_ratio
                total_duration = len(y) / sr
                if total_duration > 0:
                    vocals_duration = sum(end - start for start, end in vocals_segments)
                    vocal_ratio = min(1.0, vocals_duration / total_duration)
        except Exception as e:
            vocals_detection = None
            drums_detection = None
            vocal_ratio = 0.0
        
        # 歌曲结构检测（Verse/Chorus/Intro/Outro等）
        song_structure = None
        try:
            total_duration = len(y) / sr
            
            # 使用自相似矩阵和能量分析检测结构
            # 1. Chroma特征（用于检测和弦变化）
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_times = librosa.frames_to_time(range(chroma.shape[1]), sr=sr)
            
            # 2. 计算自相似矩阵（检测重复段落）
            # 使用简化的方法：计算时间窗口内的特征相似度
            window_size = int(8.0 * sr / 512)  # 8秒窗口（假设hop_length=512）
            if window_size < 1:
                window_size = 1
            
            # 计算MFCC特征（用于检测音色变化）
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_times = librosa.frames_to_time(range(mfcc.shape[1]), sr=sr)
            
            # 归一化RMS能量（已经计算过）
            rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
            
            # 结构段落检测
            structure_segments = {
                'intro': None,
                'verse': [],
                'chorus': [],
                'breakdown': None,
                'outro': None
            }
            
            # Intro检测（前15-30秒，能量较低）
            intro_end = min(30, total_duration * 0.15)
            if total_duration > 10:
                intro_energy = np.mean(rms_norm[:int(intro_end * len(rms_norm) / total_duration)])
                if intro_energy < 0.6:  # Intro能量通常较低
                    structure_segments['intro'] = (0.0, intro_end)
            
            # 寻找第一个Chorus（能量峰值，通常在15-60秒）
            search_start = int(intro_end * len(rms_norm) / total_duration) if structure_segments['intro'] else 0
            search_end = min(int(total_duration * 0.5), 60) * len(rms_norm) / total_duration
            search_start_idx = max(0, int(search_start))
            search_end_idx = min(len(rms_norm), int(search_end))
            
            if search_end_idx > search_start_idx:
                energy_window = rms_norm[search_start_idx:search_end_idx]
                threshold = np.mean(energy_window) + 0.3 * np.std(energy_window)
                peaks = np.where(energy_window > threshold)[0]
                
                if len(peaks) > 0:
                    first_peak_idx = peaks[0] + search_start_idx
                    first_chorus_start = rms_times[first_peak_idx] if first_peak_idx < len(rms_times) else intro_end
                    
                    # Chorus通常持续16-32小节（约30-60秒）
                    chorus_duration = min(60, total_duration * 0.15)
                    chorus_end = min(first_chorus_start + chorus_duration, total_duration * 0.8)
                    structure_segments['chorus'].append((first_chorus_start, chorus_end))
                    
                    # Verse检测（Intro到第一个Chorus之间）
                    if structure_segments['intro'] and first_chorus_start > intro_end:
                        structure_segments['verse'].append((intro_end, first_chorus_start))
            
            # Breakdown检测（能量突然下降，通常在60%-80%位置）
            if total_duration > 120:
                breakdown_start_idx = int(len(rms_norm) * 0.6)
                breakdown_end_idx = int(len(rms_norm) * 0.8)
                if breakdown_end_idx > breakdown_start_idx:
                    breakdown_window = rms_norm[breakdown_start_idx:breakdown_end_idx]
                    breakdown_idx = breakdown_start_idx + np.argmin(breakdown_window)
                    breakdown_time = rms_times[breakdown_idx] if breakdown_idx < len(rms_times) else None
                    if breakdown_time:
                        breakdown_energy = rms_norm[breakdown_idx]
                        if breakdown_energy < 0.5:  # Breakdown能量明显下降
                            structure_segments['breakdown'] = (breakdown_time, min(breakdown_time + 30, total_duration * 0.9))
            
            # Outro检测（最后10-20%）
            outro_start = max(total_duration * 0.85, total_duration - 30)
            if total_duration > 30:
                structure_segments['outro'] = (outro_start, total_duration)
            
            # 检测多个Chorus和Verse（如果有breakdown）
            if structure_segments['breakdown'] and structure_segments['chorus']:
                last_chorus_end = structure_segments['chorus'][-1][1]
                breakdown_start = structure_segments['breakdown'][0]
                
                # Breakdown前可能有第二个Verse
                if breakdown_start > last_chorus_end + 10:
                    structure_segments['verse'].append((last_chorus_end, breakdown_start))
                
                # Breakdown后可能有第二个Chorus
                breakdown_end = structure_segments['breakdown'][1]
                if breakdown_end < total_duration - 30:
                    second_chorus_start = breakdown_end
                    second_chorus_end = min(second_chorus_start + 60, total_duration * 0.9)
                    structure_segments['chorus'].append((second_chorus_start, second_chorus_end))
            
            song_structure = structure_segments
            
            # 【优化B】增强人声分段：基于 structure_segments 创建 vocal_sections
            # P0-3优化：使用enhanced_vocal_segmentation模块
            vocal_sections = {
                'verse': [],
                'chorus': [],
                'pre_chorus': []
            }
            vocal_chunk_type = {}
            try:
                # P0-3优化：使用增强人声分段检测
                try:
                    from enhanced_vocal_segmentation import detect_vocal_segments_enhanced
                    
                    enhanced_vocal_result = detect_vocal_segments_enhanced(
                        y=y, sr=sr, total_duration=total_duration,
                        existing_vocal_segments=vocals_segments if 'vocals_segments' in locals() else None,
                        structure_segments=structure_segments
                    )
                    
                    # 更新vocal_sections
                    if enhanced_vocal_result.get('vocal_sections'):
                        vocal_sections = enhanced_vocal_result['vocal_sections']
                    if enhanced_vocal_result.get('vocal_chunk_type'):
                        vocal_chunk_type = enhanced_vocal_result['vocal_chunk_type']
                    if enhanced_vocal_result.get('chorus_segments'):
                        # 确保chorus_segments已添加到structure_segments
                        if 'chorus' not in structure_segments:
                            structure_segments['chorus'] = []
                        structure_segments['chorus'].extend(enhanced_vocal_result['chorus_segments'])
                    if enhanced_vocal_result.get('verse_segments'):
                        # 确保verse_segments已添加到structure_segments
                        if 'verse' not in structure_segments:
                            structure_segments['verse'] = []
                        structure_segments['verse'].extend(enhanced_vocal_result['verse_segments'])
                    
                    # 更新vocal_segments_list
                    if enhanced_vocal_result.get('vocal_segments_detailed'):
                        vocal_segments_list = enhanced_vocal_result['vocal_segments_detailed']
                except ImportError:
                    # 模块不存在，使用原有方法
                    pass
                except Exception:
                    # 检测失败，使用原有方法
                    pass
                
                # Fallback：基于 structure_segments 和 vocal_segments 增强
                if 'vocal_segments' in locals() and vocal_segments:
                    # 将 vocal_segments 与 structure_segments 对齐
                    for verse_seg in structure_segments.get('verse', []):
                        # 检查该 verse 段内是否有人声
                        verse_vocals = [(vs, ve) for vs, ve in vocal_segments 
                                       if verse_seg[0] <= vs < verse_seg[1] or verse_seg[0] <= ve < verse_seg[1]]
                        if verse_vocals:
                            vocal_sections['verse'].extend(verse_vocals)
                    
                    for chorus_seg in structure_segments.get('chorus', []):
                        # 检查该 chorus 段内是否有人声
                        chorus_vocals = [(cs, ce) for cs, ce in vocal_segments 
                                        if chorus_seg[0] <= cs < chorus_seg[1] or chorus_seg[0] <= ce < chorus_seg[1]]
                        if chorus_vocals:
                            vocal_sections['chorus'].extend(chorus_vocals)
                    
                    # Pre-chorus 检测：在 verse 和 chorus 之间的过渡段
                    for i, verse_seg in enumerate(structure_segments.get('verse', [])):
                        if i < len(structure_segments.get('chorus', [])):
                            chorus_seg = structure_segments['chorus'][i]
                            if chorus_seg[0] > verse_seg[1]:
                                # verse 和 chorus 之间有间隔，可能是 pre-chorus
                                pre_chorus_start = verse_seg[1]
                                pre_chorus_end = chorus_seg[0]
                                pre_chorus_vocals = [(ps, pe) for ps, pe in vocal_segments 
                                                    if pre_chorus_start <= ps < pre_chorus_end or pre_chorus_start <= pe < pre_chorus_end]
                                if pre_chorus_vocals:
                                    vocal_sections['pre_chorus'].extend(pre_chorus_vocals)
                else:
                    # 如果没有 vocal_segments，基于 structure_segments 粗略估计
                    for verse_seg in structure_segments.get('verse', []):
                        # 假设 verse 段内有人声（如果 vocal_ratio > 0.3）
                        if 'vocal_ratio' in locals() and vocal_ratio > 0.3:
                            vocal_sections['verse'].append(verse_seg)
                    
                    for chorus_seg in structure_segments.get('chorus', []):
                        # 假设 chorus 段内有人声（如果 vocal_ratio > 0.3）
                        if 'vocal_ratio' in locals() and vocal_ratio > 0.3:
                            vocal_sections['chorus'].append(chorus_seg)
            except Exception:
                # 计算失败不影响主流程
                vocal_sections = {'verse': [], 'chorus': [], 'pre_chorus': []}
            
        except Exception as e:
            song_structure = None
            vocal_sections = {'verse': [], 'chorus': [], 'pre_chorus': []}
        
        # 计算repetition_score（重复度）和is_loop_or_tool（是否为Loop/Tool）
        repetition_score = 0.5  # 默认中等重复度
        is_loop_or_tool = False  # 默认不是Loop/Tool
        try:
            total_duration = len(y) / sr
            
            # 使用自相似矩阵检测重复段落
            # 计算MFCC特征的自相似度（使用已有的MFCC特征，如果已计算）
            if 'mfcc' not in locals():
                mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # 计算时间窗口内的MFCC相似度
            window_size = int(4.0 * sr / 512)  # 4秒窗口
            if window_size < 1:
                window_size = 1
            
            # 计算相邻窗口的相似度
            num_windows = max(2, mfcc.shape[1] // window_size)
            similarities = []
            for i in range(min(num_windows - 1, 10)):  # 最多比较10个窗口
                start_idx = i * window_size
                end_idx = min((i + 1) * window_size, mfcc.shape[1])
                next_start_idx = (i + 1) * window_size
                next_end_idx = min((i + 2) * window_size, mfcc.shape[1])
                
                if end_idx > start_idx and next_end_idx > next_start_idx:
                    window1 = np.mean(mfcc[:, start_idx:end_idx], axis=1)
                    window2 = np.mean(mfcc[:, next_start_idx:next_end_idx], axis=1)
                    
                    # 计算余弦相似度
                    dot_product = np.dot(window1, window2)
                    norm1 = np.linalg.norm(window1)
                    norm2 = np.linalg.norm(window2)
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        similarities.append(float(similarity))
            
            # repetition_score = 相似度的平均值
            if similarities:
                repetition_score = float(np.mean(similarities))
            
            # 判断是否为Loop/Tool（优化：提高阈值，避免误判正常歌曲）
            # 条件1：repetition_score > 0.98 且 duration < 60秒（极高重复度且极短）
            # 条件2：repetition_score > 0.95 且 duration < 30秒 且 energy > 70（极高重复度、极短、高能量）
            # 条件3：duration < 20秒（极短，通常是tool）
            # 注意：华语流行音乐重复度高（0.95-1.00）是正常现象，不应判为TOOL_LOOP
            if total_duration < 20:
                is_loop_or_tool = True
            elif repetition_score > 0.98 and total_duration < 60:
                is_loop_or_tool = True
            elif repetition_score > 0.95 and total_duration < 30 and energy_level > 70:
                is_loop_or_tool = True
            else:
                is_loop_or_tool = False
                
        except Exception:
            repetition_score = 0.5
            is_loop_or_tool = False
        
        # 检测first_drop_time（极稳4-Step Drop Detection）
        # 仅在detect_drop=True时执行，默认不检测以提升性能
        # 使用多特征检测：低频能量+6dB、Kick密度+40%、高频瞬态+35%
        first_drop_time = None
        drop_detected = False
        drop_confidence = None
        if detect_drop:
            try:
                total_duration = len(y) / sr
                if total_duration > 15:
                    # 计算8小节窗口（≈16秒，基于BPM）
                    beat_duration = 60.0 / bpm if bpm > 0 else 0.5
                    bars_8_duration = 8 * 4 * beat_duration  # 8小节 = 8 * 4拍
                    window_samples = int(bars_8_duration * sr)
                    
                    # 预先计算spectral_contrast（如果还没有计算）
                    if 'spectral_contrast' not in locals():
                        try:
                            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
                        except:
                            spectral_contrast = None
                    
                    # 使用已有的rms和rms_times（在能量分析中已计算）
                    if 'rms' in locals() and 'rms_times' in locals():
                        # 计算前15%的平均能量（Intro能量）
                        intro_end_time = min(15.0, total_duration * 0.15)
                        intro_end_idx = np.argmin(np.abs(rms_times - intro_end_time))
                        if intro_end_idx > 0 and intro_end_idx < len(rms):
                            intro_avg_energy = float(np.mean(rms[:intro_end_idx]))
                            
                            # 搜索Drop位置（在15%-60%之间）
                            search_start_idx = intro_end_idx
                            search_end_idx = min(len(rms), int(len(rms) * 0.6))
                            
                            # 方法1：低频能量检测（+6dB触发）
                            # 计算频谱的低频部分（20-200Hz）
                            S = librosa.stft(y, hop_length=512)
                            S_mag = np.abs(S)
                            # 低频能量（20-200Hz对应的频率bin）
                            low_freq_bins = librosa.fft_frequencies(sr=sr)[:int(200 * len(S_mag) / (sr/2))]
                            low_freq_mask = librosa.fft_frequencies(sr=sr) <= 200
                            low_freq_energy = np.mean(S_mag[low_freq_mask, :], axis=0)
                            
                            # 方法2：Kick密度检测（+30%触发，从40%优化到30%以提高敏感度）
                            # 使用HPSS分离打击乐部分
                            D = librosa.stft(y)
                            D_harm, D_perc = librosa.decompose.hpss(D)
                            perc_energy = np.mean(np.abs(D_perc), axis=0)
                            
                            # 方法3：高频瞬态检测（+35%触发）
                            # 计算高频能量（2kHz以上）
                            high_freq_mask = librosa.fft_frequencies(sr=sr) >= 2000
                            high_freq_energy = np.mean(S_mag[high_freq_mask, :], axis=0)
                            
                            # 在8小节窗口内检测Drop
                            for i in range(search_start_idx, search_end_idx):
                                if i + window_samples >= len(low_freq_energy):
                                    continue
                                
                                # 计算窗口内的变化
                                window_start = max(0, i - window_samples)
                                window_end = min(len(low_freq_energy), i + window_samples)
                                
                                if window_end - window_start < window_samples:
                                    continue
                                
                                # 1. 低频能量变化（+6dB = 约2倍）
                                low_before = np.mean(low_freq_energy[window_start:i])
                                low_after = np.mean(low_freq_energy[i:window_end])
                                if low_before > 0:
                                    low_db_change = 20 * np.log10(low_after / low_before) if low_after > 0 else 0
                                else:
                                    low_db_change = 0
                                
                                # 2. Kick密度变化（+30%，从40%优化到30%以提高敏感度）
                                kick_before = np.mean(perc_energy[window_start:i])
                                kick_after = np.mean(perc_energy[i:window_end])
                                if kick_before > 0:
                                    kick_density_change = (kick_after - kick_before) / kick_before
                                else:
                                    kick_density_change = 0
                                
                                # 3. 高频瞬态变化（+35%）
                                high_before = np.mean(high_freq_energy[window_start:i])
                                high_after = np.mean(high_freq_energy[i:window_end])
                                if high_before > 0:
                                    transient_change = (high_after - high_before) / high_before
                                else:
                                    transient_change = 0
                                
                                # ========== 优化：改进Drop检测 - 权重系统（替代简单计数） ==========
                                # 为不同特征赋予权重，而不是简单的计数
                                # 这样对于subtle制作手法（如Deep House/Minimal Techno）也能准确检测
                                drop_score = 0.0
                                
                                # 低频能量变化（最强指标，权重0.4）
                                if low_db_change >= 6:
                                    drop_score += 0.4
                                
                                # Kick密度变化（权重0.3）
                                if kick_density_change >= 0.30:  # 从0.40优化到0.30
                                    drop_score += 0.3
                                
                                # 高频瞬态变化（权重0.2）
                                if transient_change >= 0.35:
                                    drop_score += 0.2
                                
                                # 频谱对比度变化检测（高频能量突增，权重0.2）
                                contrast_change = 0.0
                                if spectral_contrast is not None:
                                    try:
                                        contrast_idx = int(i * len(spectral_contrast[0]) / len(rms_times))
                                        contrast_start = max(0, contrast_idx - 10)
                                        contrast_end = min(spectral_contrast.shape[1], contrast_idx + 10)
                                        if contrast_end > contrast_start:
                                            spectral_contrast_window = spectral_contrast[:, contrast_start:contrast_end]
                                            mid_point = spectral_contrast_window.shape[1] // 2
                                            contrast_before = np.mean(spectral_contrast_window[:, :mid_point]) if mid_point > 0 else 0
                                            contrast_after = np.mean(spectral_contrast_window[:, mid_point:]) if mid_point < spectral_contrast_window.shape[1] else 0
                                            if contrast_before > 0:
                                                contrast_change = (contrast_after - contrast_before) / contrast_before
                                                if contrast_change >= 0.25:  # 频谱对比度上升25%
                                                    drop_score += 0.2
                                    except:
                                        pass
                                
                                # 阈值判断：0.5分即可（意味着强特征1个 或 弱特征2个）
                                # 这样对于subtle制作手法也能检测到Drop
                                drop_detected = drop_score >= 0.5
                                drop_confidence = float(max(0.0, min(1.0, drop_score)))
                                
                                if drop_detected:
                                    # 转换为时间
                                    first_drop_time = float(rms_times[i])
                                    break
            except Exception:
                first_drop_time = None
        
        # ========== 【优化D】Drop 16/32拍对齐：计算 drop_beat_position、breakdown_position、bar_structure ==========
        drop_beat_position = None
        breakdown_position = None
        bar_structure = {}
        try:
            if 'beat_times' in locals() and len(beat_times) > 0 and bpm > 0:
                beat_duration = 60.0 / bpm
                
                # 1. 计算 drop_beat_position（将 first_drop_time 转换为第几拍）
                if first_drop_time is not None:
                    # 找到最接近的 beat
                    drop_beat_idx = np.argmin(np.abs(beat_times - first_drop_time))
                    drop_beat_position = int(drop_beat_idx)  # 第几拍（从0开始）
                
                # 2. 计算 breakdown_position（基于 structure_segments）
                if 'structure_segments' in locals() and structure_segments.get('breakdown'):
                    breakdown_time = structure_segments['breakdown'][0]
                    breakdown_beat_idx = np.argmin(np.abs(beat_times - breakdown_time))
                    breakdown_position = int(breakdown_beat_idx)
                
                # 3. 计算 bar_structure（基于 structure_segments，转换为小节数）
                if 'structure_segments' in locals():
                    beats_per_bar_val = beats_per_bar if beats_per_bar > 0 else 4
                    
                    def time_to_bars(time_sec):
                        if time_sec is None:
                            return None
                        beats = time_sec / beat_duration
                        return int(beats / beats_per_bar_val) if beats_per_bar_val > 0 else 0
                    
                    if structure_segments.get('intro'):
                        intro_length = structure_segments['intro'][1] - structure_segments['intro'][0]
                        bar_structure['intro'] = time_to_bars(intro_length)
                    
                    if structure_segments.get('verse'):
                        verse_lengths = [v[1] - v[0] for v in structure_segments['verse']]
                        bar_structure['verse'] = [time_to_bars(vl) for vl in verse_lengths]
                    
                    if structure_segments.get('chorus'):
                        chorus_lengths = [c[1] - c[0] for c in structure_segments['chorus']]
                        bar_structure['chorus'] = [time_to_bars(cl) for cl in chorus_lengths]
                    
                    if structure_segments.get('breakdown'):
                        breakdown_length = structure_segments['breakdown'][1] - structure_segments['breakdown'][0]
                        bar_structure['breakdown'] = time_to_bars(breakdown_length)
                    
                    if structure_segments.get('outro'):
                        outro_length = structure_segments['outro'][1] - structure_segments['outro'][0]
                        bar_structure['outro'] = time_to_bars(outro_length)
        except Exception:
            # 计算失败不影响主流程
            pass
        
        # 风格检测（基于BPM和音频特征）
        genre = None
        try:
            # 基于BPM和能量特征的简单风格分类
            if bpm < 90:
                genre = "Downtempo/Ambient"
            elif 90 <= bpm < 110:
                genre = "Hip-Hop/Dubstep"
            elif 110 <= bpm < 120:
                genre = "House"
            elif 120 <= bpm < 130:
                if energy_level > 70:
                    genre = "Tech House/Progressive House"
                else:
                    genre = "Deep House"
            elif 130 <= bpm < 140:
                genre = "House/UK Garage"
            elif 140 <= bpm < 150:
                genre = "Trance/Progressive"
            elif 150 <= bpm < 170:
                genre = "Hardstyle/Techno"
            elif bpm >= 170:
                genre = "Hardcore/Drum & Bass"
            
            # 根据节拍强度调整
            if beat_strength > 0.8 and bpm >= 120:
                if genre == "House":
                    genre = "Tech House"
                elif genre == "Trance/Progressive":
                    genre = "Hard Trance"
        except:
            genre = None
        
        # 初始化状态变量
        key_status = 'DETECTED' if detected_key else 'UNKNOWN'
        bpm_status = 'DETECTED'
        
        # ========== 新增：共识BPM检测（如果启用） ==========
        try:
            # 尝试导入配置管理器
            try:
                from config_manager import get_config
                config = get_config() or {}
            except ImportError:
                config = {}
            enable_consensus = config.get('analysis.enable_consensus_detection', True)
            
            if enable_consensus and 'y' in locals() and 'sr' in locals():
                from consensus_detector import consensus_bpm_detection
                
                # 共识BPM检测（使用已加载的音频数据，避免重复加载）
                # 注意：这里y和sr在函数作用域内应该可用（从deep_analyze_track的参数）
                final_bpm, final_bpm_confidence = consensus_bpm_detection(
                    file_path=file_path,
                    primary_bpm=bpm,
                    primary_confidence=bpm_confidence,
                    y=y,  # 传递已加载的音频数据
                    sr=sr  # 传递采样率
                )
                
                if final_bpm > 0:
                    # 如果共识BPM与当前BPM差异>2，标记为冲突
                    if abs(final_bpm - bpm) > 2:
                        bpm_status = 'CONFLICT'
                        # 使用平均BPM，但降低置信度
                        bpm = (bpm + final_bpm) / 2.0
                        bpm_confidence = min(bpm_confidence, final_bpm_confidence) * 0.7
                    else:
                        # 差异小，使用共识结果
                        bpm = final_bpm
                        bpm_confidence = max(bpm_confidence, final_bpm_confidence)
        except ImportError:
            pass  # 共识检测器未找到，使用原结果
        except Exception:
            pass  # 共识检测失败，使用原结果
        
        # ========== 新增：高级律动 / 音色 / 瞬态 / Hook 特征 ==========
        groove_swing = None
        groove_offset = None
        bass_pattern = None
        tone_low_ratio = None
        tone_mid_ratio = None
        tone_high_ratio = None
        kick_hardness = None
        snare_hardness = None
        vocal_mood = None
        hook_strength = None
        try:
            # Groove swing：使用节拍间隔的相对标准差粗略衡量律动松紧
            if len(beat_times) >= 4:
                beat_intervals = np.diff(beat_times)
                if len(beat_intervals) > 1:
                    interval_mean = float(np.mean(beat_intervals))
                    interval_std = float(np.std(beat_intervals))
                    if interval_mean > 0:
                        groove_swing = max(0.0, min(1.0, interval_std / interval_mean))
            # 频段平衡：低/中/高频能量比例
            S = np.abs(librosa.stft(y=y, n_fft=1024, hop_length=512)) ** 2
            freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
            total_energy = float(S.sum())
            if total_energy > 0:
                low_mask = freqs < 120
                mid_mask = (freqs >= 120) & (freqs < 4000)
                high_mask = freqs >= 4000
                tone_low_ratio = float(S[low_mask].sum() / total_energy)
                tone_mid_ratio = float(S[mid_mask].sum() / total_energy)
                tone_high_ratio = float(S[high_mask].sum() / total_energy)
                if tone_low_ratio > 0.4:
                    bass_pattern = "bass_heavy"
                elif tone_low_ratio < 0.2:
                    bass_pattern = "bass_light"
                else:
                    bass_pattern = "bass_balanced"
            # 瞬态硬度：用整体 RMS 的峰值与均值比值近似
            frame_rms = librosa.feature.rms(y=y)[0]
            if len(frame_rms) > 0:
                peak = float(frame_rms.max())
                rms_mean = float(frame_rms.mean())
                if rms_mean > 0:
                    hardness_db = 20.0 * np.log10((peak + 1e-6) / (rms_mean + 1e-6))
                    hardness_norm = max(0.0, min(hardness_db / 20.0, 1.0))
                    kick_hardness = float(hardness_norm)
                    snare_hardness = float(hardness_norm)
                    
                    # ========== 【修复8】使用 kick_hardness 进一步确认 Hardstyle ==========
                    # 如果之前标记为 hardstyle，但 kick_hardness 不够高，可能是误判
                    try:
                        if 'drum_pattern' in locals() and locals().get('drum_pattern') == "hardstyle":
                            if kick_hardness < 0.6 and four_on_floor_kick_ratio < 0.9:
                                # kick_hardness 不够高，可能是其他高BPM风格
                                drum_pattern = "four_on_floor"
                                drum_group = "4x4"
                    except:
                        pass  # 如果 drum_pattern 还未定义，跳过
            # Hook 强度：复用重复度评分
            if 'repetition_score' in locals():
                hook_strength = float(repetition_score)
            # Vocal 情绪标签（修复：调整阈值，能量平均值约35，需要更合理的分界）
            key_for_mood = detected_key or ""
            energy_for_mood = min(100, max(0, energy_level))
            
            # 修复：降低Instrumental阈值，提高检测率
            if vocal_ratio < 0.15:
                vocal_mood = "Instrumental"
            else:
                is_major = key_for_mood.endswith("B")  # Camelot B 视为大调
                # 修复：调整能量阈值（从65降到45），因为能量平均值约35
                # 同时加入brightness作为辅助判断
                brightness_for_mood = brightness if 'brightness' in locals() else 0.5
                
                if is_major and (energy_for_mood >= 45 or brightness_for_mood > 0.6):
                    vocal_mood = "Happy"
                elif is_major and energy_for_mood < 45:
                    vocal_mood = "Chill"
                elif not is_major and energy_for_mood >= 50:
                    vocal_mood = "Aggressive"
                elif not is_major and energy_for_mood < 30:
                    vocal_mood = "Dark"
                else:
                    # 中等能量的小调歌曲，根据brightness判断
                    if brightness_for_mood > 0.5:
                        vocal_mood = "Chill"
                    else:
                        vocal_mood = "Dark"
        except Exception:
            # 任何分析失败都不影响主流程
            pass
        
        # ========== 【优化C】Valence 情绪值：计算 valence 和 arousal ==========
        valence = 0.5  # 默认中性
        arousal = 0.5  # 默认中等能量
        try:
            # 1. 计算 spectral_centroid（已有，复用）
            if 'spectral_centroids' not in locals():
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_centroid_mean = float(np.mean(spectral_centroids))
            
            # 2. 计算 MFCC（已有，复用）
            if 'mfcc' not in locals():
                mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfcc, axis=1)
            # MFCC 明亮度：前3个MFCC系数的平均值（越高越明亮）
            mfcc_brightness = float(np.mean(mfcc_mean[1:4])) if len(mfcc_mean) >= 4 else 0.0
            
            # 3. 判断 mode（大调/小调）
            is_major = False
            if detected_key:
                # Camelot B = 大调，A = 小调
                is_major = detected_key.endswith("B")
            
            # 4. 计算高频能量比例（用于判断明亮度）
            if 'tone_high_ratio' in locals() and tone_high_ratio is not None:
                high_freq_ratio = float(tone_high_ratio)
            else:
                # 如果没有，临时计算
                S = np.abs(librosa.stft(y=y, n_fft=1024, hop_length=512)) ** 2
                freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
                total_energy = float(S.sum())
                if total_energy > 0:
                    high_mask = freqs >= 4000
                    high_freq_ratio = float(S[high_mask].sum() / total_energy)
                else:
                    high_freq_ratio = 0.3
            
            # 5. 组合计算 Valence（情绪值：0=暗黑/忧郁，1=快乐/明亮）
            # 公式：valence = (spectral_centroid_norm + mfcc_brightness_norm + mode_bonus + high_freq_norm) / 4
            spectral_centroid_norm = max(0.0, min(1.0, (spectral_centroid_mean - 1000) / 3000))  # 1000-4000Hz 映射到 0-1
            mfcc_brightness_norm = max(0.0, min(1.0, (mfcc_brightness + 10) / 20))  # -10到10 映射到 0-1
            mode_bonus = 0.15 if is_major else -0.15  # 大调+0.15，小调-0.15
            high_freq_norm = max(0.0, min(1.0, high_freq_ratio * 2.0))  # 0-0.5 映射到 0-1
            
            valence = max(0.0, min(1.0, (spectral_centroid_norm + mfcc_brightness_norm + mode_bonus + high_freq_norm) / 4.0))
            
            # 6. 计算 Arousal（能量/唤醒度：0=平静，1=高能量）
            # 基于 energy_level 和 onset_strength（节拍强度）
            energy_norm = min(100, max(0, energy_level)) / 100.0
            
            # 修复：beat_strength是beat帧索引的平均值（几千），不是能量值
            # 改用onset_strength来计算节拍强度的归一化值
            try:
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                if onset_env is not None and len(onset_env) > 0:
                    # 使用onset强度的90分位数作为节拍强度指标
                    onset_90th = float(np.percentile(onset_env, 90))
                    onset_max = float(np.max(onset_env))
                    # 归一化到0-1范围
                    beat_strength_norm = onset_90th / (onset_max + 1e-6) if onset_max > 0 else 0.5
                    beat_strength_norm = max(0.0, min(1.0, beat_strength_norm))
                else:
                    beat_strength_norm = 0.5
            except Exception:
                beat_strength_norm = 0.5
            
            arousal = max(0.0, min(1.0, (energy_norm * 0.7 + beat_strength_norm * 0.3)))
            
        except Exception:
            # 计算失败使用默认值
            valence = 0.5
            arousal = 0.5
        
        # P1-2优化：情绪滑动窗口计算
        emotion_sliding_window = []
        valence_window_mean = valence
        arousal_window_mean = arousal
        valence_window_std = 0.0
        arousal_window_std = 0.0
        try:
            total_duration = len(y) / sr
            window_duration = 8.0  # 8秒窗口
            window_hop = 4.0  # 4秒步进
            
            if total_duration > window_duration:
                num_windows = int((total_duration - window_duration) / window_hop) + 1
                window_valences = []
                window_arousals = []
                
                for i in range(num_windows):
                    start_time = i * window_hop
                    end_time = min(start_time + window_duration, total_duration)
                    
                    start_sample = int(start_time * sr)
                    end_sample = int(end_time * sr)
                    
                    if end_sample > start_sample and end_sample <= len(y):
                        window_audio = y[start_sample:end_sample]
                        
                        try:
                            # 计算窗口内的valence和arousal
                            # 复用上面的计算逻辑，但只对窗口音频
                            window_sc = librosa.feature.spectral_centroid(y=window_audio, sr=sr)[0]
                            window_sc_mean = float(np.mean(window_sc))
                            
                            window_mfcc = librosa.feature.mfcc(y=window_audio, sr=sr, n_mfcc=13)
                            window_mfcc_mean = np.mean(window_mfcc, axis=1)
                            window_mfcc_brightness = float(np.mean(window_mfcc_mean[1:4])) if len(window_mfcc_mean) >= 4 else 0.0
                            
                            # 使用全局的is_major（简化）
                            mode_bonus = 0.15 if is_major else -0.15
                            
                            # 高频能量
                            window_S = np.abs(librosa.stft(y=window_audio, n_fft=1024, hop_length=512)) ** 2
                            window_freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
                            window_total_energy = float(window_S.sum())
                            if window_total_energy > 0:
                                window_high_mask = window_freqs >= 4000
                                window_high_freq_ratio = float(window_S[window_high_mask].sum() / window_total_energy)
                            else:
                                window_high_freq_ratio = 0.3
                            
                            # 计算窗口valence
                            window_sc_norm = max(0.0, min(1.0, (window_sc_mean - 1000) / 3000))
                            window_mfcc_norm = max(0.0, min(1.0, (window_mfcc_brightness + 10) / 20))
                            window_high_norm = max(0.0, min(1.0, window_high_freq_ratio * 2.0))
                            window_valence = max(0.0, min(1.0, (window_sc_norm + window_mfcc_norm + mode_bonus + window_high_norm) / 4.0))
                            
                            # 计算窗口arousal（基于能量）
                            window_rms = librosa.feature.rms(y=window_audio)[0]
                            window_energy = float(np.mean(window_rms))
                            # 归一化到0-1（基于全局RMS范围）
                            if 'rms' in locals():
                                global_rms_max = float(np.max(rms)) if hasattr(rms, 'max') else 0.1
                                window_energy_norm = min(1.0, window_energy / (global_rms_max + 1e-6))
                            else:
                                window_energy_norm = 0.5
                            
                            # 计算窗口beat strength
                            try:
                                window_onset_env = librosa.onset.onset_strength(y=window_audio, sr=sr)
                                window_beat_strength = float(np.mean(window_onset_env)) if len(window_onset_env) > 0 else 0.5
                            except:
                                window_beat_strength = 0.5
                            
                            window_arousal = max(0.0, min(1.0, (window_energy_norm * 0.7 + window_beat_strength * 0.3)))
                            
                            window_valences.append(window_valence)
                            window_arousals.append(window_arousal)
                            
                            emotion_sliding_window.append({
                                'time': round(start_time, 2),
                                'valence': round(window_valence, 3),
                                'arousal': round(window_arousal, 3)
                            })
                        except Exception:
                            # 窗口计算失败，跳过
                            continue
                
                if window_valences and window_arousals:
                    valence_window_mean = float(np.mean(window_valences))
                    arousal_window_mean = float(np.mean(window_arousals))
                    valence_window_std = float(np.std(window_valences))
                    arousal_window_std = float(np.std(window_arousals))
        except Exception:
            # 滑动窗口计算失败，使用全局值
            emotion_sliding_window = []
            valence_window_mean = valence
            arousal_window_mean = arousal
            valence_window_std = 0.0
            arousal_window_std = 0.0

        # ============================================================
        # ROI 新增维度（轻量，失败可回退；用于更职业的自动排 set）
        # A) 乐句/段落边界：8/16/32 小节对齐标记 + 推荐 mix in/out 别名
        # B) 人声时间线：合并后的 vocal_regions + intro/outro vocal_ratio（不二次读盘）
        # C) 调性漂移：tonal_stability + key_modulations（弱化“不稳定key”的硬惩罚）
        # ============================================================
        _roi_cfg = {}
        try:
            from config_manager import get_config as _get_cfg  # type: ignore
            _roi_cfg = _get_cfg() or {}
        except Exception:
            _roi_cfg = {}
        _roi_phrase_enabled = bool(_roi_cfg.get("analysis.enable_roi_phrase_markers", True))
        _roi_vocal_enabled = bool(_roi_cfg.get("analysis.enable_roi_vocal_timeline", True))
        _roi_tonal_enabled = bool(_roi_cfg.get("analysis.enable_roi_tonal_drift", True))

        phrase_markers = {}
        recommended_mix_in = mix_in_point
        recommended_mix_out = mix_out_point
        try:
            if not _roi_phrase_enabled:
                raise RuntimeError("roi_phrase_disabled")
            _bpb = int(beats_per_bar) if isinstance(beats_per_bar, (int, float)) else 4
            if _bpb not in (3, 4):
                _bpb = 4
            phrase_markers["beats_per_bar"] = _bpb
            if 'beat_times' in locals() and beat_times is not None and len(beat_times) >= _bpb * 16:
                def _mk(bars: int, limit: int = 30):
                    step = int(bars * _bpb)
                    out = []
                    for i in range(step, len(beat_times), step):
                        out.append(round(float(beat_times[i]), 2))
                        if len(out) >= limit:
                            break
                    return out
                phrase_markers["bars_8"] = _mk(8)
                phrase_markers["bars_16"] = _mk(16)
                phrase_markers["bars_32"] = _mk(32)
        except Exception:
            phrase_markers = {}

        vocal_regions = []
        intro_vocal_ratio = None
        outro_vocal_ratio = None
        try:
            if not _roi_vocal_enabled:
                raise RuntimeError("roi_vocal_disabled")
            total_duration = float(len(y) / sr) if sr else None
            regions_src = None
            if 'vocal_segments_list' in locals() and isinstance(vocal_segments_list, list) and vocal_segments_list:
                regions_src = vocal_segments_list
            elif 'vocal_sections' in locals() and isinstance(vocal_sections, dict) and vocal_sections:
                tmp = []
                for _k, segs in (vocal_sections or {}).items():
                    if isinstance(segs, list):
                        tmp.extend(segs)
                regions_src = tmp

            if regions_src:
                cleaned = []
                for s, e in regions_src:
                    try:
                        s = float(s); e = float(e)
                        if e <= s:
                            continue
                        if total_duration:
                            s = max(0.0, min(s, total_duration))
                            e = max(0.0, min(e, total_duration))
                        cleaned.append((s, e))
                    except Exception:
                        continue
                cleaned.sort(key=lambda x: x[0])
                merged = []
                for s, e in cleaned:
                    if not merged or s > merged[-1][1]:
                        merged.append([s, e])
                    else:
                        merged[-1][1] = max(merged[-1][1], e)
                vocal_regions = [(round(a, 2), round(b, 2)) for a, b in merged[:40]]

            if total_duration and vocal_regions:
                def _overlap(a0, a1, b0, b1):
                    return max(0.0, min(a1, b1) - max(a0, b0))
                intro0, intro1 = 0.0, min(30.0, total_duration)
                outro0, outro1 = max(0.0, total_duration - 30.0), total_duration
                intro_cov = 0.0
                outro_cov = 0.0
                for s, e in vocal_regions:
                    intro_cov += _overlap(s, e, intro0, intro1)
                    outro_cov += _overlap(s, e, outro0, outro1)
                intro_vocal_ratio = float(intro_cov / max(1e-6, (intro1 - intro0)))
                outro_vocal_ratio = float(outro_cov / max(1e-6, (outro1 - outro0)))
        except Exception:
            vocal_regions = []
            intro_vocal_ratio = None
            outro_vocal_ratio = None

        tonal_stability = None
        key_modulations = []
        try:
            if not _roi_tonal_enabled:
                raise RuntimeError("roi_tonal_disabled")
            # 复用已算过的 chroma（若不存在则用 chroma_stft 轻量补齐）
            if librosa is not None and np is not None:
                _chroma = None
                _times = None
                if 'chroma' in locals() and chroma is not None and getattr(chroma, "shape", (0, 0))[1] >= 20:
                    _chroma = chroma
                    # librosa.feature.chroma_cqt 默认 hop_length=512
                    _times = librosa.frames_to_time(np.arange(_chroma.shape[1]), sr=sr, hop_length=512)
                else:
                    hop = 2048
                    _chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop, n_fft=4096)
                    _times = librosa.frames_to_time(np.arange(_chroma.shape[1]), sr=sr, hop_length=hop)

                if _chroma is not None and _times is not None and _chroma.shape[1] >= 20:
                    major_prof = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88], dtype=np.float32)
                    minor_prof = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17], dtype=np.float32)
                    major_prof /= (np.linalg.norm(major_prof) + 1e-6)
                    minor_prof /= (np.linalg.norm(minor_prof) + 1e-6)
                    note_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

                    def _best_key(ch_vec):
                        v = np.array(ch_vec, dtype=np.float32)
                        v = v / (np.linalg.norm(v) + 1e-6)
                        best_k = "C:maj"
                        best_s = -1.0
                        for r in range(12):
                            smaj = float(np.dot(v, np.roll(major_prof, r)))
                            smi = float(np.dot(v, np.roll(minor_prof, r)))
                            if smaj > best_s:
                                best_k, best_s = f"{note_names[r]}:maj", smaj
                            if smi > best_s:
                                best_k, best_s = f"{note_names[r]}:min", smi
                        return best_k, best_s

                    total_duration = float(len(y) / sr) if sr else 0.0
                    if total_duration > 20:
                        win = 10.0
                        step = 5.0
                        keys = []
                        strengths = []
                        t = 0.0
                        while t + win <= total_duration + 1e-3:
                            mask = (_times >= t) & (_times < t + win)
                            idxs = np.where(mask)[0]
                            if idxs.size >= 2:
                                ch_mean = np.mean(_chroma[:, idxs], axis=1)
                                k, s = _best_key(ch_mean)
                                keys.append(k)
                                strengths.append(s)
                            t += step

                        if keys:
                            from collections import Counter
                            c = Counter(keys)
                            main_key, main_cnt = c.most_common(1)[0]
                            stability_ratio = float(main_cnt / max(1, len(keys)))
                            strength_mean = float(np.mean(strengths)) if strengths else 0.0
                            tonal_stability = float(max(0.0, min(1.0, stability_ratio * (strength_mean / 1.2))))

                            # 连续2个窗口以上偏离主key -> 记录为 modulation（很保守，避免误报）
                            cur = None
                            start = None
                            streak = 0
                            for i, k in enumerate(keys):
                                seg_t = i * step
                                if k != main_key:
                                    if cur == k:
                                        streak += 1
                                    else:
                                        if cur and streak >= 1 and start is not None:
                                            key_modulations.append({"start": round(float(start), 1), "end": round(float(seg_t + win), 1), "key": str(cur)})
                                        cur = k
                                        start = seg_t
                                        streak = 0
                                else:
                                    if cur and streak >= 1 and start is not None:
                                        key_modulations.append({"start": round(float(start), 1), "end": round(float(seg_t + win), 1), "key": str(cur)})
                                    cur = None
                                    start = None
                                    streak = 0
                            if cur and streak >= 1 and start is not None:
                                key_modulations.append({"start": round(float(start), 1), "end": round(float(min(total_duration, (len(keys)-1)*step + win)), 1), "key": str(cur)})
                            key_modulations = key_modulations[:8]
        except Exception:
            tonal_stability = None
            key_modulations = []

        result = {
            'bpm': round(bpm, 1),
            'bpm_confidence': round(float(bpm_confidence), 3),  # BPM可信度（0-1）
            'beat_stability': round(float(beat_stability), 3),  # 拍点稳定性（0-1）
            'time_signature': time_signature,  # 拍号（4/4、3/4等）
            'time_signature_confidence': round(float(time_signature_confidence), 3),  # 拍号置信度（0-1）
            'beats_per_bar': beats_per_bar,  # 每小节拍数
            'energy': min(100, max(0, energy_level)),
            'duration': len(y) / sr,
            'beat_strength': float(beat_strength),
            'onset_count': len(onset_times),
            'key': detected_key,  # 如果检测到调性，返回；否则为None，使用数据库中的
            'key_confidence': round(float(key_confidence), 3),  # Key可信度（0-1）
            'key_status': key_status,  # Key状态
            'bpm_status': bpm_status,  # BPM状态
            'mix_in_point': round(mix_in_point, 2) if mix_in_point else None,  # 最佳混入点（秒）
            'mix_out_point': round(mix_out_point, 2) if mix_out_point else None,  # 最佳混出点（秒）
            # ROI-A：别名（便于排序器/报告统一字段名）
            'recommended_mix_in': round(float(recommended_mix_in), 2) if isinstance(recommended_mix_in, (int, float)) else None,
            'recommended_mix_out': round(float(recommended_mix_out), 2) if isinstance(recommended_mix_out, (int, float)) else None,
            'genre': genre,  # 检测到的风格
            'genre_tag': genre_tag,  # 风格标签（Deep/Chill, House/Tech, DnB/Hard）- 用于排序辅助参考
            'structure': song_structure,  # 歌曲结构：Intro/Verse/Chorus/Breakdown/Outro
            'vocals': vocals_detection,  # 人声检测结果
            'vocal_ratio': round(float(vocal_ratio), 3),  # 人声比例（0-1）
            'drums': drums_detection,  # 鼓点检测结果
            'energy_profile': energy_profile,
            'rms_mean': rms_global if 'rms_global' in locals() else None,
            'onset_mean': onset_global if 'onset_global' in locals() else None,
            'downbeat_offset': round(downbeat_offset, 3),  # 强拍偏移（秒）- 用于强拍对齐检测
            # P0-1优化：Ensemble检测结果
            'downbeat_confidence': round(float(downbeat_confidence), 3),  # Ensemble置信度（0-1）
            'needs_manual_alignment': needs_manual_alignment,  # 是否需要人工审查
            'beatgrid_fix_hint': beatgrid_fix_hint,  # 修正建议文本
            'ensemble_metadata': ensemble_metadata,  # Ensemble检测详细元数据
            'repetition_score': round(float(repetition_score), 3),  # 重复度（0-1）
            'is_loop_or_tool': bool(is_loop_or_tool),  # 是否为Loop/Tool
            'first_drop_time': round(first_drop_time, 2) if first_drop_time else None,  # 第一个Drop位置（秒）
            'drop_detected': bool(drop_detected) if 'drop_detected' in locals() else False,  # Drop是否被检测到
            'drop_status': 'DETECTED' if (first_drop_time is not None and drop_detected) else None,  # Drop状态
            'drop_confidence': round(float(drop_confidence), 3) if drop_confidence is not None else None,  # Drop置信度（0-1）
            # 新增高级特征
            'groove_swing': round(float(groove_swing), 3) if groove_swing is not None else None,
            'groove_offset': groove_offset,
            'bass_pattern': bass_pattern,
            'tone_low_ratio': round(float(tone_low_ratio), 4) if tone_low_ratio is not None else None,
            'tone_mid_ratio': round(float(tone_mid_ratio), 4) if tone_mid_ratio is not None else None,
            'tone_high_ratio': round(float(tone_high_ratio), 4) if tone_high_ratio is not None else None,
            'kick_hardness': round(float(kick_hardness), 3) if kick_hardness is not None else None,
            'snare_hardness': round(float(snare_hardness), 3) if snare_hardness is not None else None,
            'vocal_mood': vocal_mood,
            'hook_strength': round(float(hook_strength), 3) if hook_strength is not None else None,
            # 新增增强模块输出（仅用于软规则打分，不会作为硬过滤条件）
            'vocal_presence': round(float(vocal_presence), 3),
            'vocal_segments': vocal_segments_list,
            'drum_pattern': drum_pattern,
            'drum_group': drum_group,  # 【优化A】鼓型分组
            'drum_pattern_subtype': drum_pattern_subtype if 'drum_pattern_subtype' in locals() else None,  # P1-3优化：鼓型子类型
            'groove_density': round(float(groove_density_value), 3) if groove_density_value is not None else None,
            'snare_peak_at_3rd_beat_ratio': round(float(snare_peak_at_3rd_beat_ratio), 3),  # 【优化A】
            'four_on_floor_kick_ratio': round(float(four_on_floor_kick_ratio), 3),  # 【优化A】
            'phrase_length': int(phrase_length_beats),
            'phrase_confidence': round(float(phrase_confidence), 3),
            'phrase_boundaries': phrase_boundaries if 'phrase_boundaries' in locals() else [],  # P1-1优化：多尺度检测的乐句边界
            'phrase_markers': phrase_markers if isinstance(phrase_markers, dict) else {},
            # 【优化B】增强人声分段（P0-3优化）
            'vocal_sections': vocal_sections if 'vocal_sections' in locals() else {'verse': [], 'chorus': [], 'pre_chorus': []},
            'vocal_chunk_type': vocal_chunk_type if 'vocal_chunk_type' in locals() else {},  # P0-3优化：人声类型标记
            # ROI-B：人声时间线（用于更稳的“避开vocal-on-vocal”）
            'vocal_regions': vocal_regions if isinstance(vocal_regions, list) else [],
            'intro_vocal_ratio': round(float(intro_vocal_ratio), 3) if isinstance(intro_vocal_ratio, (int, float)) else None,
            'outro_vocal_ratio': round(float(outro_vocal_ratio), 3) if isinstance(outro_vocal_ratio, (int, float)) else None,
            # ROI-C：调性漂移（用于弱化“不稳定key”的硬惩罚）
            'tonal_stability': round(float(tonal_stability), 3) if isinstance(tonal_stability, (int, float)) else None,
            'key_modulations': key_modulations if isinstance(key_modulations, list) else [],
            # 【优化C】Valence 情绪值
            'valence': round(float(valence), 3),
            'arousal': round(float(arousal), 3),
            # P1-2优化：情绪滑动窗口
            'emotion_sliding_window': emotion_sliding_window,  # 滑动窗口情绪时间序列
            'valence_window_mean': round(float(valence_window_mean), 3),  # 平均valence
            'arousal_window_mean': round(float(arousal_window_mean), 3),  # 平均arousal
            'valence_window_std': round(float(valence_window_std), 3),  # valence标准差（变化程度）
            'arousal_window_std': round(float(arousal_window_std), 3),  # arousal标准差（变化程度）
            # 【优化D】Drop 16/32拍对齐
            'drop_beat_position': drop_beat_position,
            'breakdown_position': breakdown_position,
            'bar_structure': bar_structure,
        }

        # ========== 新增：通用DJ实务维度（P0） ==========
        # 注意：尽量复用已加载的 y/sr，避免二次读盘
        try:
            extra = analyze_mix_metrics_light(y=y, sr=sr, bpm=bpm, beat_times=beat_times, file_path=file_path)
            if isinstance(extra, dict) and extra:
                result.update(extra)
        except Exception:
            pass
        
        # ========== 新增：二次DROP检测（如果主检测器失败） ==========
        if first_drop_time is None and detect_drop:
            try:
                # 尝试导入配置管理器
                try:
                    from config_manager import get_config
                    config = get_config() or {}
                except ImportError:
                    config = {}
                enable_secondary = config.get('analysis.enable_secondary_drop_detector', True)
                secondary_confidence_threshold = config.get('analysis.drop_secondary_confidence', 0.6)
                fallback_enabled = config.get('analysis.fallback_to_energy_envelope', True)
                
                if enable_secondary:
                    from secondary_drop_detector import secondary_drop_detector, estimate_drop_by_energy_envelope
                    
                    # 检查是否为Mashup/Remix
                    file_name = os.path.basename(file_path).lower()
                    is_mashup = any(kw in file_name for kw in ['mashup', 'edit', 'remix', 'bootleg', 'club edit'])
                    
                    # 运行二次检测器
                    drop_time, confidence = secondary_drop_detector(file_path, sr=sr, duration_limit=max_duration)
                    
                    if drop_time and confidence >= secondary_confidence_threshold:
                        # 二次检测成功
                        result['first_drop_time'] = round(drop_time, 2)
                        result['drop_detected'] = True
                        result['drop_status'] = 'DETECTED'
                        result['drop_confidence'] = round(confidence, 3)
                    elif fallback_enabled and drop_time:
                        # 使用稳健回退策略
                        result['first_drop_time'] = round(drop_time, 2)
                        result['drop_detected'] = False  # 标记为估计值
                        result['drop_status'] = 'ESTIMATED'
                        result['drop_confidence'] = round(confidence, 3)
                    elif fallback_enabled:
                        # 完全回退：使用能量包络估计
                        estimated_drop = estimate_drop_by_energy_envelope(y, sr)
                        result['first_drop_time'] = round(estimated_drop, 2)
                        result['drop_detected'] = False
                        result['drop_status'] = 'ESTIMATED'
                        result['drop_confidence'] = 0.4  # 低置信度
            except ImportError:
                # 二次检测器未找到，跳过
                pass
            except Exception as e:
                # 二次检测失败，跳过
                pass
        
        return result
    except Exception as e:
        return None

def strict_bpm_dj_sort(tracks: list, max_bpm_diff: float = 12.0) -> list:
    """
    严格BPM限制的专业DJ排序算法
    确保相邻歌曲BPM跨度不超过max_bpm_diff
    
    Parameters:
    - tracks: 歌曲列表
    - max_bpm_diff: 最大BPM跨度（默认12）
    
    Returns:
    - 排序后的歌曲列表
    """
    
    if not tracks:
        return []
    
    # 准备数据
    for i, track in enumerate(tracks):
        track['_index'] = i
        track['_used'] = False
    
    sorted_tracks = []
    remaining_tracks = tracks.copy()
    
    # 选择起始点：最低BPM + 低能量
    start_track = min(remaining_tracks, 
                     key=lambda t: (t.get('energy', 0), t.get('bpm', 0)))
    sorted_tracks.append(start_track)
    remaining_tracks.remove(start_track)
    
    current_track = start_track
    max_iterations = len(tracks) * 5  # 增加迭代次数，因为限制更严格
    iteration = 0
    
    while remaining_tracks and iteration < max_iterations:
        iteration += 1
        
        # 找到所有BPM跨度在限制内的候选歌曲
        valid_candidates = []
        for track in remaining_tracks:
            if strict_bpm_check(current_track.get('bpm', 0), 
                               track.get('bpm', 0), 
                               max_bpm_diff):
                valid_candidates.append(track)
        
        # 如果找不到BPM跨度在限制内的歌曲，尝试放宽限制（但不超过15）
        if not valid_candidates and max_bpm_diff < 15:
            for track in remaining_tracks:
                if strict_bpm_check(current_track.get('bpm', 0), 
                                   track.get('bpm', 0), 
                                   15.0):
                    valid_candidates.append(track)
        
        # 如果还是没有候选，使用所有剩余歌曲（但标记为警告）
        if not valid_candidates:
            valid_candidates = remaining_tracks[:min(10, len(remaining_tracks))]
        
        # 计算每个候选的得分
        candidates = []
        for track in valid_candidates:
            score = 0
            
            # BPM兼容性（40%权重）- 优先选择BPM接近的
            bpm_diff = abs(current_track.get('bpm', 0) - track.get('bpm', 0))
            if bpm_diff <= 2:
                score += 40
            elif bpm_diff <= 5:
                score += 35
            elif bpm_diff <= 8:
                score += 30
            elif bpm_diff <= 12:
                score += 25
            else:
                score += 10  # 超过12但仍在允许范围内
            
            # 调性兼容性（30%权重）
            key_score = get_key_compatibility(
                current_track.get('key', ''),
                track.get('key', '')
            )
            score += key_score * 0.3
            
            # 能量渐进（30%权重）- 允许适度的能量变化
            energy_diff = track.get('energy', 0) - current_track.get('energy', 0)
            if -10 <= energy_diff <= 10:  # 允许小幅波动
                score += 30
            elif 10 < energy_diff <= 20:  # 适度上升
                score += 25
            elif -20 <= energy_diff < -10:  # 适度下降
                score += 20
            else:
                score += 10  # 大幅变化扣分
            
            # 如果BPM跨度超过12，大幅扣分
            if bpm_diff > 12:
                score -= 50
            
            candidates.append((score, track, bpm_diff))
        
        # 如果没有候选，退出
        if not candidates:
            break
        
        # 按得分排序，优先选择得分高的
        candidates.sort(key=lambda x: (x[0], -x[2]), reverse=True)  # 得分高，BPM差小
        best_score, best_track, bpm_diff = candidates[0]
        
        # 如果得分太低且BPM跨度超过12，标记警告
        if bpm_diff > max_bpm_diff:
            best_track['_bpm_warning'] = True
            best_track['_bpm_diff'] = bpm_diff
        
        # 添加到排序列表
        sorted_tracks.append(best_track)
        remaining_tracks.remove(best_track)
        current_track = best_track
    
    # 如果还有剩余歌曲，按BPM和调性兼容性添加到末尾
    if remaining_tracks:
        remaining_tracks.sort(key=lambda t: (
            abs(current_track.get('bpm', 0) - t.get('bpm', 0)),
            -get_key_compatibility(current_track.get('key', ''), t.get('key', ''))
        ))
        sorted_tracks.extend(remaining_tracks)
    
    return sorted_tracks

async def create_strict_bpm_multi_set(playlist_name: str = "流行Boiler Room",
                                     songs_per_set: int = 40,
                                     min_songs_per_set: int = 35,
                                     max_songs_per_set: int = 45,
                                     max_bpm_diff: float = 12.0):
    """
    创建严格BPM限制的多Set排序
    
    Parameters:
    - playlist_name: 播放列表名称
    - songs_per_set: 每个set的歌曲数（目标）
    - min_songs_per_set: 每个set最少歌曲数
    - max_songs_per_set: 每个set最多歌曲数
    - max_bpm_diff: 相邻歌曲最大BPM跨度（默认12）
    """
    
    # 连接数据库
    db = RekordboxDatabase()
    
    try:
        print("正在连接到Rekordbox数据库...")
        await db.connect()
        print("连接成功！")
        
        # 查找播放列表
        all_playlists = await db.get_playlists()
        target_playlist = None
        
        # 首先尝试使用ID（如果输入的是数字）
        if playlist_name.isdigit():
            try:
                # ID可能是字符串或整数，尝试两种匹配方式
                playlist_id_str = str(playlist_name)
                playlist_id_int = int(playlist_name)
                for p in all_playlists:
                    # 尝试字符串匹配和整数匹配
                    if (str(p.id) == playlist_id_str or 
                        (isinstance(p.id, int) and p.id == playlist_id_int) or
                        (isinstance(p.id, str) and p.id == playlist_id_str)):
                        target_playlist = p
                        break
            except:
                pass
        
        # 如果ID匹配失败，尝试名称匹配
        if not target_playlist:
            playlist_name_lower = playlist_name.lower().strip()
            for p in all_playlists:
                if p.name:
                    try:
                        p_name_lower = p.name.lower().strip()
                        # 完全匹配或包含匹配
                        if (playlist_name_lower == p_name_lower or 
                            playlist_name_lower in p_name_lower or 
                            p_name_lower in playlist_name_lower):
                            target_playlist = p
                            break
                    except:
                        # 如果编码有问题，尝试字节匹配
                        try:
                            p_name_bytes = p.name.encode('utf-8', errors='ignore').lower()
                            playlist_name_bytes = playlist_name.encode('utf-8', errors='ignore').lower()
                            if playlist_name_bytes in p_name_bytes or p_name_bytes in playlist_name_bytes:
                                target_playlist = p
                                break
                        except:
                            pass
        
        if not target_playlist:
            try:
                safe_name = playlist_name.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
                print(f"Playlist not found: {safe_name}")
                print("Available playlists:")
                for p in all_playlists[:20]:
                    if p.name:
                        try:
                            safe_pname = p.name.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
                            if safe_pname:
                                print(f"  - {safe_pname}")
                        except:
                            pass
            except Exception as e:
                print(f"Error: {e}")
            await db.disconnect()
            return
        
        safe_playlist_name = target_playlist.name.encode('utf-8', errors='ignore').decode('utf-8')
        try:
            print(f"找到播放列表: {safe_playlist_name}")
        except:
            print(f"Found playlist: {safe_playlist_name}")
        
        # 获取播放列表中的歌曲
        try:
            tracks = await db.get_playlist_tracks(target_playlist.id)
        except Exception as e:
            # 如果get_playlist_tracks失败，使用pyrekordbox直接查询
            from pyrekordbox import Rekordbox6Database
            pyrekordbox_db = Rekordbox6Database()
            playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=target_playlist.id))
            tracks = []
            for song in playlist_songs:
                if getattr(song, 'rb_local_deleted', 0) == 0:
                    content = pyrekordbox_db.get_content(ContentID=song.ContentID)
                    if content:
                        from rekordbox_mcp.database import Track
                        track = Track(
                            id=content.ID,
                            title=content.Title or "",
                            artist=content.ArtistName or "",
                            file_path=content.FilePath or "",
                            bpm=content.Tempo / 100.0 if content.Tempo else None,
                            key=content.KeyName or "",
                            energy=None
                        )
                        tracks.append(track)
        
        if not tracks:
            try:
                print("播放列表为空")
            except UnicodeEncodeError:
                print("Playlist is empty")
            await db.disconnect()
            return
        
        try:
            print(f"播放列表中共有 {len(tracks)} 首歌曲")
            print("\n开始深度分析每首歌曲（使用librosa）...")
        except UnicodeEncodeError:
            print(f"Playlist has {len(tracks)} tracks")
            print("\nStarting deep analysis (using librosa)...")
        analyzed_tracks = []
        deep_analysis_count = 0
        
        for idx, track in enumerate(tracks, 1):
            file_path = track.file_path if hasattr(track, 'file_path') else None
            
            if not file_path or not os.path.exists(file_path):
                # 尝试从数据库获取路径
                try:
                    from pyrekordbox import Rekordbox6Database
                    from sqlalchemy import text
                    pyrekordbox_db = Rekordbox6Database()
                    path_query = text("SELECT Path FROM djmdContent WHERE ID = :content_id")
                    path_result = pyrekordbox_db.session.execute(
                        path_query, {"content_id": track.id}
                    ).fetchone()
                    if path_result and path_result[0]:
                        file_path = path_result[0]
                        if not os.path.exists(file_path):
                            # 尝试常见路径
                            potential_paths = [
                                os.path.join(r"D:\song", os.path.basename(file_path)),
                                file_path,
                            ]
                            for pp in potential_paths:
                                if os.path.exists(pp):
                                    file_path = pp
                                    break
                except:
                    pass
            
            # 准备track数据
            db_bpm = track.bpm if hasattr(track, 'bpm') and track.bpm else None
            track_data = {
                'id': track.id,
                'title': track.title or "",
                'artist': track.artist or "",
                'file_path': file_path or "",
                'bpm': db_bpm,
                'key': track.key if hasattr(track, 'key') else "",
                'energy': None
            }
            
            # 深度分析（传入数据库BPM用于验证）
            if file_path and os.path.exists(file_path):
                analysis = deep_analyze_track(file_path, db_bpm=db_bpm)
                if analysis:
                    track_data['bpm'] = analysis['bpm']
                    track_data['energy'] = analysis['energy']
                    track_data['duration'] = analysis.get('duration', 0)
                    deep_analysis_count += 1
                    try:
                        db_bpm_str = f", DB_BPM: {db_bpm:.1f}" if db_bpm else ""
                        print(f"  [{idx:03d}/{len(tracks)}] 分析: {track_data['title'][:40]} "
                              f"(BPM: {track_data['bpm']:.1f}{db_bpm_str}, Energy: {track_data['energy']})")
                    except UnicodeEncodeError:
                        print(f"  [{idx:03d}/{len(tracks)}] 分析完成 (BPM: {track_data['bpm']:.1f}, Energy: {track_data['energy']})")
                else:
                    # 分析失败，使用数据库中的BPM
                    if not track_data['bpm']:
                        track_data['bpm'] = 120.0  # 默认值
                    track_data['energy'] = 50  # 默认能量
            else:
                # 文件不存在，使用数据库中的BPM
                if not track_data['bpm']:
                    track_data['bpm'] = 120.0  # 默认值
                track_data['energy'] = 50  # 默认能量
            
            analyzed_tracks.append(track_data)
        
        try:
            print(f"\n深度分析完成: {deep_analysis_count}/{len(tracks)} 首歌曲")
            print(f"\n开始排序（BPM跨度限制: {max_bpm_diff}）...")
        except UnicodeEncodeError:
            print(f"\nDeep analysis complete: {deep_analysis_count}/{len(tracks)} tracks")
            print(f"\nStarting sort (BPM diff limit: {max_bpm_diff})...")
        sorted_tracks = strict_bpm_dj_sort(analyzed_tracks, max_bpm_diff)
        
        # 检查BPM跨度
        bpm_warnings = []
        for i in range(len(sorted_tracks) - 1):
            current_bpm = sorted_tracks[i].get('bpm', 0)
            next_bpm = sorted_tracks[i + 1].get('bpm', 0)
            diff = abs(current_bpm - next_bpm)
            if diff > max_bpm_diff:
                bpm_warnings.append({
                    'index': i + 1,
                    'current': sorted_tracks[i].get('title', ''),
                    'next': sorted_tracks[i + 1].get('title', ''),
                    'diff': diff
                })
        
        if bpm_warnings:
            try:
                print(f"\n警告: 发现 {len(bpm_warnings)} 处BPM跨度超过 {max_bpm_diff}:")
                for w in bpm_warnings[:5]:
                    try:
                        print(f"  [{w['index']}] {w['current'][:30]} → {w['next'][:30]} (跨度: {w['diff']:.1f})")
                    except UnicodeEncodeError:
                        print(f"  [{w['index']}] BPM跨度: {w['diff']:.1f}")
            except UnicodeEncodeError:
                print(f"\nWarning: {len(bpm_warnings)} BPM jumps exceed {max_bpm_diff}")
        
        # 分割成多个set
        num_sets = (len(sorted_tracks) + songs_per_set - 1) // songs_per_set
        try:
            print(f"\n将歌曲分成 {num_sets} 个Set（每个约 {songs_per_set} 首）...")
            sets = []
            for i in range(num_sets):
                start_idx = i * songs_per_set
                end_idx = min((i + 1) * songs_per_set, len(sorted_tracks))
                set_tracks = sorted_tracks[start_idx:end_idx]
                sets.append(set_tracks)
                print(f"  Set {i+1}: {len(set_tracks)} 首歌曲")
        except UnicodeEncodeError:
            print(f"\nDividing into {num_sets} sets (about {songs_per_set} tracks each)...")
            sets = []
            for i in range(num_sets):
                start_idx = i * songs_per_set
                end_idx = min((i + 1) * songs_per_set, len(sorted_tracks))
                set_tracks = sorted_tracks[start_idx:end_idx]
                sets.append(set_tracks)
                print(f"  Set {i+1}: {len(set_tracks)} tracks")
        
        # 生成M3U文件
        output_dir = Path(r"D:\生成的set")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        playlist_display_name = target_playlist.name or playlist_name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        m3u_file = output_dir / f"{playlist_display_name}_严格BPM_{num_sets}个Set_{timestamp}.m3u"
        
        m3u_lines = ["#EXTM3U"]
        m3u_lines.append(f"#PLAYLIST:{playlist_display_name} - {num_sets}个Set (BPM跨度≤{max_bpm_diff})")
        m3u_lines.append("")
        
        total_tracks = 0
        for set_num in range(1, num_sets + 1):
            set_tracks = sets[set_num - 1]
            
            # Set标题
            m3u_lines.append(f"#  ========== Set {set_num}/{num_sets} ({len(set_tracks)}首) ==========")
            
            # 如果是第二个set开始，添加分隔符（复制上一set的最后一首）
            if set_num > 1:
                last_track = sets[set_num - 2][-1]
                title = last_track.get('title', '')
                artist = last_track.get('artist', '')
                file_path = last_track.get('file_path', '')
                if file_path:
                    separator_title = f"【分割线】Set {set_num-1}→{set_num} - {title} - {artist}"
                    m3u_lines.append(f"#EXTINF:-1,{separator_title}")
                    m3u_lines.append(file_path)
                    total_tracks += 1
            
            # 添加当前set的歌曲
            for track in set_tracks:
                title = track.get('title', '')
                artist = track.get('artist', '')
                file_path = track.get('file_path', '')
                bpm = track.get('bpm', 0)
                energy = track.get('energy', 0)
                
                if file_path:
                    display_name = f"{title} - {artist} [BPM:{bpm:.1f} E:{energy}]"
                    m3u_lines.append(f"#EXTINF:-1,{display_name}")
                    m3u_lines.append(file_path)
                    total_tracks += 1
            
            m3u_lines.append("")  # Set之间空行
        
        # 保存M3U文件
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))
        
        # 生成详细报告
        report_file = output_dir / f"{playlist_display_name}_严格BPM排序报告_{timestamp}.txt"
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("严格BPM多Set排序报告")
        report_lines.append("=" * 100)
        report_lines.append(f"播放列表: {playlist_display_name}")
        report_lines.append(f"总歌曲数: {len(sorted_tracks)} 首")
        report_lines.append(f"Set数量: {num_sets} 个")
        report_lines.append(f"每个Set: 约 {songs_per_set} 首")
        report_lines.append(f"BPM跨度限制: ≤ {max_bpm_diff}")
        report_lines.append(f"深度分析: {deep_analysis_count}/{len(sorted_tracks)} 首")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        if bpm_warnings:
            report_lines.append(f"⚠️ 警告: 发现 {len(bpm_warnings)} 处BPM跨度超过 {max_bpm_diff}")
            report_lines.append("")
            for w in bpm_warnings:
                try:
                    report_lines.append(f"  [{w['index']}] {w['current']} → {w['next']} (跨度: {w['diff']:.1f})")
                except:
                    report_lines.append(f"  [{w['index']}] BPM跨度: {w['diff']:.1f}")
            report_lines.append("")
        
        report_lines.append("=" * 100)
        report_lines.append("Set详情")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        for set_num in range(1, num_sets + 1):
            set_tracks = sets[set_num - 1]
            report_lines.append(f"Set {set_num}/{num_sets} ({len(set_tracks)}首)")
            report_lines.append("-" * 100)
            
            for idx, track in enumerate(set_tracks, 1):
                title = track.get('title', '')
                artist = track.get('artist', '')
                bpm = track.get('bpm', 0)
                key = track.get('key', '')
                energy = track.get('energy', 0)
                
                # 计算与前一首的BPM差
                if idx > 1:
                    prev_bpm = set_tracks[idx - 2].get('bpm', 0)
                    bpm_diff = abs(bpm - prev_bpm)
                    diff_str = f" (Δ{bpm_diff:+.1f})"
                    if bpm_diff > max_bpm_diff:
                        diff_str += " ⚠️"
                else:
                    diff_str = ""
                
                try:
                    report_lines.append(f"  [{idx:02d}] {title} - {artist}")
                    report_lines.append(f"       BPM: {bpm:.1f}{diff_str} | Key: {key} | Energy: {energy}")
                except UnicodeEncodeError:
                    report_lines.append(f"  [{idx:02d}] {title.encode('utf-8', errors='ignore').decode('utf-8')}")
                    report_lines.append(f"       BPM: {bpm:.1f}{diff_str} | Key: {key} | Energy: {energy}")
            
            report_lines.append("")
        
        report_lines.append("=" * 100)
        report_lines.append("统计信息")
        report_lines.append("=" * 100)
        
        # BPM跨度统计
        all_diffs = []
        for i in range(len(sorted_tracks) - 1):
            diff = abs(sorted_tracks[i].get('bpm', 0) - sorted_tracks[i + 1].get('bpm', 0))
            all_diffs.append(diff)
        
        if all_diffs:
            avg_diff = sum(all_diffs) / len(all_diffs)
            max_diff = max(all_diffs)
            min_diff = min(all_diffs)
            within_limit = sum(1 for d in all_diffs if d <= max_bpm_diff)
            
            report_lines.append(f"平均BPM跨度: {avg_diff:.2f}")
            report_lines.append(f"最大BPM跨度: {max_diff:.2f}")
            report_lines.append(f"最小BPM跨度: {min_diff:.2f}")
            report_lines.append(f"在限制内: {within_limit}/{len(all_diffs)} ({within_limit*100/len(all_diffs):.1f}%)")
        
        report_lines.append("")
        report_lines.append(f"M3U文件: {m3u_file.name}")
        report_lines.append(f"报告文件: {report_file.name}")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        try:
            print(f"\n{'='*50}")
            print("排序完成！")
            print(f"Set数量: {num_sets} 个")
            print(f"总歌曲数: {len(sorted_tracks)} 首")
            print(f"深度分析: {deep_analysis_count}/{len(sorted_tracks)} 首")
            if all_diffs:
                print(f"平均BPM跨度: {avg_diff:.2f}")
                print(f"在限制内: {within_limit}/{len(all_diffs)} ({within_limit*100/len(all_diffs):.1f}%)")
            print(f"\nM3U文件: {m3u_file}")
            print(f"报告文件: {report_file}")
        except UnicodeEncodeError:
            print(f"\n{'='*50}")
            print("Sort complete!")
            print(f"Sets: {num_sets}")
            print(f"Total tracks: {len(sorted_tracks)}")
            print(f"Deep analysis: {deep_analysis_count}/{len(sorted_tracks)}")
            if all_diffs:
                print(f"Avg BPM diff: {avg_diff:.2f}")
                print(f"Within limit: {within_limit}/{len(all_diffs)} ({within_limit*100/len(all_diffs):.1f}%)")
            print(f"\nM3U file: {m3u_file}")
            print(f"Report file: {report_file}")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            await db.disconnect()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='严格BPM多Set排序工具')
    parser.add_argument('playlist', nargs='?', default='流行Boiler Room',
                       help='播放列表名称（默认: 流行Boiler Room）')
    parser.add_argument('--songs-per-set', type=int, default=40,
                       help='每个set的歌曲数（默认: 40）')
    parser.add_argument('--max-bpm-diff', type=float, default=12.0,
                       help='相邻歌曲最大BPM跨度（默认: 12.0）')
    
    args = parser.parse_args()
    
    asyncio.run(create_strict_bpm_multi_set(
        playlist_name=args.playlist,
        songs_per_set=args.songs_per_set,
        max_bpm_diff=args.max_bpm_diff
    ))

