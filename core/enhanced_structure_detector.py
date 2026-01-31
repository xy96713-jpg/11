#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版结构识别模块
使用能量包络 + percussive ratio + spectral flux 多重交叉确认
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


def detect_structure_enhanced(
    audio_file: str,
    bpm: Optional[float] = None,
    duration: Optional[float] = None,
    sample_rate: int = 22050
) -> Dict:
    """
    增强版结构识别
    
    使用3个检测点交叉确认：
    1. 能量包络（RMS）
    2. Percussive Ratio（打击乐比例）
    3. Spectral Flux（频谱通量）
    
    Returns:
        Dict包含：
        - structure.breakdown: (start, end) 秒
        - structure.build_up: (start, end) 秒
        - structure.drop: (start, end) 秒
        - structure.outro: (start, end) 秒
        - structure.intro: (start, end) 秒
        - confidence: 置信度分数 (0-1)
    """
    if not HAS_LIBROSA:
        return _get_default_structure(duration or 180.0)
    
    try:
        # 加载音频
        y, sr = librosa.load(audio_file, sr=sample_rate, duration=duration)
        actual_duration = len(y) / sr
        
        # 如果BPM未知，检测BPM
        if bpm is None or bpm <= 0:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        
        # ========== 检测点1：能量包络（RMS） ==========
        rms_results = _detect_structure_by_rms(y, sr, bpm, actual_duration)
        
        # ========== 检测点2：Percussive Ratio ==========
        perc_results = _detect_structure_by_percussive(y, sr, bpm, actual_duration)
        
        # ========== 检测点3：Spectral Flux ==========
        flux_results = _detect_structure_by_spectral_flux(y, sr, bpm, actual_duration)
        
        # ========== 检测点4：Energy History (New Precision Layer) ==========
        history_results = _detect_structure_by_energy_history(y, sr, bpm, actual_duration)
        
        # ========== 交叉确认 ==========
        structure = _cross_validate_structure(
            rms_results, perc_results, flux_results, history_results, actual_duration, bpm
        )
        
        return structure
        
    except Exception as e:
        print(f"结构识别失败: {e}")
        return _get_default_structure(duration or 180.0)


def _detect_structure_by_rms(
    y: np.ndarray, sr: int, bpm: float, duration: float
) -> Dict:
    """使用RMS能量包络检测结构"""
    try:
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
        rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
        
        # 计算能量变化率（一阶导数）
        rms_diff = np.diff(rms_norm)
        rms_diff_times = rms_times[1:]
        
        # 检测Drop：能量突然大幅上升
        drop_candidates = []
        for i in range(1, len(rms_diff)):
            if rms_diff[i] > 0.3:  # 能量突然上升30%以上
                drop_candidates.append((rms_diff_times[i], rms_diff[i]))
        
        # 选择能量上升最大的点作为Drop
        drop_time = None
        if drop_candidates:
            drop_time = max(drop_candidates, key=lambda x: x[1])[0]
        else:
            # 默认Drop在30-40%处
            drop_time = duration * 0.35
        
        # 检测Breakdown：能量突然下降
        breakdown_candidates = []
        for i in range(1, len(rms_diff)):
            if rms_diff[i] < -0.2:  # 能量突然下降20%以上
                breakdown_candidates.append((rms_diff_times[i], abs(rms_diff[i])))
        
        breakdown_time = None
        if breakdown_candidates:
            breakdown_time = max(breakdown_candidates, key=lambda x: x[1])[0]
        
        # 检测Build-up：Drop前的能量逐渐上升
        build_up_start = None
        build_up_end = drop_time
        if drop_time:
            # 在Drop前32拍（8小节）寻找能量逐渐上升的区域
            beat_duration = 60.0 / bpm
            build_up_duration = 32 * beat_duration  # 32拍
            build_up_start_time = max(0, drop_time - build_up_duration)
            
            # 找到能量开始上升的点
            build_up_start_idx = np.argmin(np.abs(rms_times - build_up_start_time))
            build_up_end_idx = np.argmin(np.abs(rms_times - drop_time))
            
            if build_up_end_idx > build_up_start_idx:
                build_up_rms = rms_norm[build_up_start_idx:build_up_end_idx]
                if len(build_up_rms) > 0:
                    # 找到能量最低点作为Build-up开始
                    min_idx = np.argmin(build_up_rms)
                    build_up_start = rms_times[build_up_start_idx + min_idx]
        
        # 检测Intro：前15%能量较低且稳定
        intro_end = duration * 0.15
        intro_rms = rms_norm[rms_times < intro_end]
        if len(intro_rms) > 0:
            intro_avg = np.mean(intro_rms)
            # 找到能量开始上升的点
            for i, t in enumerate(rms_times):
                if t < intro_end and rms_norm[i] > intro_avg * 1.2:
                    intro_end = t
                    break
        
        # 检测Outro：最后20%能量下降
        outro_start = duration * 0.8
        outro_rms = rms_norm[rms_times > outro_start]
        if len(outro_rms) > 0:
            outro_avg = np.mean(outro_rms)
            # 找到能量开始下降的点
            for i in range(len(rms_times) - 1, -1, -1):
                t = rms_times[i]
                if t > outro_start and rms_norm[i] < outro_avg * 0.8:
                    outro_start = t
                    break
        
        return {
            'drop': (drop_time - 2.0, drop_time + 2.0) if drop_time else None,
            'breakdown': (breakdown_time - 2.0, breakdown_time + 2.0) if breakdown_time else None,
            'build_up': (build_up_start, build_up_end) if build_up_start and build_up_end else None,
            'intro': (0.0, intro_end),
            'outro': (outro_start, duration),
            'confidence': 0.7
        }
    except Exception:
        return _get_default_structure(duration)


def _detect_structure_by_percussive(
    y: np.ndarray, sr: int, bpm: float, duration: float
) -> Dict:
    """使用Percussive Ratio检测结构"""
    try:
        # 分离谐波和打击乐成分
        D = librosa.stft(y)
        D_harm, D_perc = librosa.decompose.hpss(D)
        
        # 计算打击乐能量
        perc_power = np.abs(D_perc) ** 2
        total_power = np.abs(D) ** 2
        
        # 计算每帧的percussive ratio
        frame_length = 2048
        hop_length = 512
        n_frames = perc_power.shape[1]
        perc_ratio = np.zeros(n_frames)
        
        for i in range(n_frames):
            perc_sum = np.sum(perc_power[:, i])
            total_sum = np.sum(total_power[:, i]) + 1e-6
            perc_ratio[i] = perc_sum / total_sum
        
        perc_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)
        
        # 归一化
        perc_norm = (perc_ratio - np.min(perc_ratio)) / (np.max(perc_ratio) - np.min(perc_ratio) + 1e-6)
        
        # 检测Drop：打击乐比例突然上升
        perc_diff = np.diff(perc_norm)
        perc_diff_times = perc_times[1:]
        
        drop_candidates = []
        for i in range(1, len(perc_diff)):
            if perc_diff[i] > 0.25:  # 打击乐比例上升25%以上
                drop_candidates.append((perc_diff_times[i], perc_diff[i]))
        
        drop_time = None
        if drop_candidates:
            drop_time = max(drop_candidates, key=lambda x: x[1])[0]
        else:
            drop_time = duration * 0.35
        
        # 检测Breakdown：打击乐比例下降
        breakdown_candidates = []
        for i in range(1, len(perc_diff)):
            if perc_diff[i] < -0.15:
                breakdown_candidates.append((perc_diff_times[i], abs(perc_diff[i])))
        
        breakdown_time = None
        if breakdown_candidates:
            breakdown_time = max(breakdown_candidates, key=lambda x: x[1])[0]
        
        # 检测Outro：最后20%打击乐比例下降
        outro_start = duration * 0.8
        outro_perc = perc_norm[perc_times > outro_start]
        if len(outro_perc) > 0:
            outro_avg = np.mean(outro_perc)
            for i in range(len(perc_times) - 1, -1, -1):
                t = perc_times[i]
                if t > outro_start and perc_norm[i] < outro_avg * 0.7:
                    outro_start = t
                    break
        
        return {
            'drop': (drop_time - 2.0, drop_time + 2.0) if drop_time else None,
            'breakdown': (breakdown_time - 2.0, breakdown_time + 2.0) if breakdown_time else None,
            'build_up': None,
            'intro': (0.0, duration * 0.15),
            'outro': (outro_start, duration),
            'confidence': 0.6
        }
    except Exception:
        return _get_default_structure(duration)


def _detect_structure_by_spectral_flux(
    y: np.ndarray, sr: int, bpm: float, duration: float
) -> Dict:
    """使用Spectral Flux检测结构"""
    try:
        # 计算频谱通量（Spectral Flux）
        # 频谱通量衡量频谱变化的速度，可以检测结构变化
        frame_length = 2048
        hop_length = 512
        
        # 计算短时傅里叶变换
        stft = librosa.stft(y, hop_length=hop_length, n_fft=frame_length)
        magnitude = np.abs(stft)
        
        # 计算频谱通量（相邻帧之间的差异）
        flux = np.zeros(magnitude.shape[1] - 1)
        for i in range(len(flux)):
            diff = magnitude[:, i+1] - magnitude[:, i]
            # 只计算正向变化（能量增加）
            flux[i] = np.sum(np.maximum(diff, 0))
        
        flux_times = librosa.frames_to_time(np.arange(len(flux)), sr=sr, hop_length=hop_length)
        flux_norm = (flux - np.min(flux)) / (np.max(flux) - np.min(flux) + 1e-6)
        
        # 检测Drop：频谱通量突然大幅上升
        flux_diff = np.diff(flux_norm)
        flux_diff_times = flux_times[1:]
        
        drop_candidates = []
        for i in range(1, len(flux_diff)):
            if flux_diff[i] > 0.3:  # 频谱通量上升30%以上
                drop_candidates.append((flux_diff_times[i], flux_diff[i]))
        
        drop_time = None
        if drop_candidates:
            drop_time = max(drop_candidates, key=lambda x: x[1])[0]
        else:
            drop_time = duration * 0.35
        
        # 检测Breakdown：频谱通量下降
        breakdown_candidates = []
        for i in range(1, len(flux_diff)):
            if flux_diff[i] < -0.2:
                breakdown_candidates.append((flux_diff_times[i], abs(flux_diff[i])))
        
        breakdown_time = None
        if breakdown_candidates:
            breakdown_time = max(breakdown_candidates, key=lambda x: x[1])[0]
        
        return {
            'drop': (drop_time - 2.0, drop_time + 2.0) if drop_time else None,
            'breakdown': (breakdown_time - 2.0, breakdown_time + 2.0) if breakdown_time else None,
            'build_up': None,
            'intro': (0.0, duration * 0.15),
            'outro': (duration * 0.8, duration),
            'confidence': 0.65
        }
    except Exception:
        return _get_default_structure(duration)


def _cross_validate_structure(
    rms_results: Dict,
    perc_results: Dict,
    flux_results: Dict,
    duration: float,
    bpm: float
) -> Dict:
    """交叉确认3个检测点的结果"""
    
    # 合并结果，取平均值或多数投票
    def merge_time_range(results: List[Optional[Tuple[float, float]]], default: Tuple[float, float]) -> Tuple[float, float]:
        valid_results = [r for r in results if r is not None]
        if not valid_results:
            return default
        
        # 取中位数
        starts = [r[0] for r in valid_results]
        ends = [r[1] for r in valid_results]
        return (np.median(starts), np.median(ends))
    
    # Drop：至少2个检测点确认
    drop_results = [rms_results.get('drop'), perc_results.get('drop'), flux_results.get('drop')]
    drop_count = sum(1 for r in drop_results if r is not None)
    
    if drop_count >= 2:
        drop = merge_time_range(drop_results, (duration * 0.35 - 2.0, duration * 0.35 + 2.0))
        drop_confidence = min(0.95, 0.6 + drop_count * 0.1)
    else:
        drop = (duration * 0.35 - 2.0, duration * 0.35 + 2.0)
        drop_confidence = 0.5
    
    # Breakdown：至少2个检测点确认
    breakdown_results = [rms_results.get('breakdown'), perc_results.get('breakdown'), flux_results.get('breakdown')]
    breakdown_count = sum(1 for r in breakdown_results if r is not None)
    
    if breakdown_count >= 2:
        breakdown = merge_time_range(breakdown_results, None)
        breakdown_confidence = min(0.9, 0.5 + breakdown_count * 0.15)
    else:
        breakdown = None
        breakdown_confidence = 0.3
    
    # Build-up：使用RMS结果（最准确）
    build_up = rms_results.get('build_up')
    build_up_confidence = 0.7 if build_up else 0.3
    
    # Intro：合并结果
    intro_results = [rms_results.get('intro'), perc_results.get('intro'), flux_results.get('intro')]
    intro = merge_time_range(intro_results, (0.0, duration * 0.15))
    intro_confidence = 0.8
    
    # Outro：合并结果
    outro_results = [rms_results.get('outro'), perc_results.get('outro'), flux_results.get('outro')]
    outro = merge_time_range(outro_results, (duration * 0.8, duration))
    outro_confidence = 0.8
    
    # 整体置信度
    overall_confidence = np.mean([
        drop_confidence,
        breakdown_confidence if breakdown else 0.5,
        build_up_confidence,
        intro_confidence,
        outro_confidence
    ])
    
    return {
        'structure': {
            'chorus': drop,       # Drop -> Chorus (Peak)
            'breakdown': breakdown,
            'build_up': build_up,
            'intro': intro,
            'outro': outro
        },
        'confidence': overall_confidence,
        'drop_confidence': drop_confidence,
        'breakdown_confidence': breakdown_confidence,
        'build_up_confidence': build_up_confidence,
        'intro_confidence': intro_confidence,
        'outro_confidence': outro_confidence,
        # 新增：语义标签
        'labels': {
            'peak': drop[0] if drop else None,
            'energy_up': build_up[0] if build_up else None,
            'energy_down': breakdown[0] if breakdown else None
        }
    }


def _detect_structure_by_energy_history(
    y: np.ndarray, sr: int, bpm: float, duration: float
) -> Dict:
    """
    使用“能量历史滑动窗口 (Energy History)”算法检测结构
    灵感来源于 skills.sh 的 BeatDetector 模式
    """
    try:
        # 计算每一帧能量 (Amplitude Squared)
        hop_length = 512
        # 使用 librosa 的能量计算
        energy = librosa.feature.rms(y=y, hop_length=hop_length)[0] ** 2
        times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
        
        # 滑动窗口大小 (约 1 秒历史)
        history_size = int(sr / hop_length) 
        sensitivity = 1.3 # 敏感度系数
        
        beats = []
        for i in range(history_size, len(energy)):
            # 计算历史平均能量
            history_avg = np.mean(energy[i-history_size:i])
            # 如果当前能量超过平均值的 sensitivity 倍，视为能量峰值 (Potential Beat/Drop)
            if energy[i] > history_avg * sensitivity:
                beats.append(times[i])
        
        # 分析能量峰值密度
        # 如果某个区间内峰值密度突然增加，通常是 Drop 开始
        if not beats:
            return _get_default_structure(duration)
            
        # 统计每 8 秒内的能量峰值密度
        interval = 8.0
        bins = np.arange(0, duration + interval, interval)
        hist, _ = np.histogram(beats, bins=bins)
        
        # 寻找密度激增点
        diff = np.diff(hist)
        drop_idx = np.argmax(diff)
        drop_time = bins[drop_idx + 1]
        
        return {
            'drop': (drop_time - 1.0, drop_time + 1.0),
            'confidence': 0.8
        }
    except Exception:
        return _get_default_structure(duration)


def _cross_validate_structure(
    rms_results: Dict,
    perc_results: Dict,
    flux_results: Dict,
    history_results: Dict,
    duration: float,
    bpm: float
) -> Dict:
    """交叉确认4个检测点的结果（含 Energy History）"""
    
    # 合并结果，取平均值或多数投票
    def merge_time_range(results: List[Optional[Tuple[float, float]]], default: Tuple[float, float]) -> Tuple[float, float]:
        valid_results = [r for r in results if r is not None]
        if not valid_results:
            return default
        
        # 取中位数
        starts = [r[0] for r in valid_results]
        ends = [r[1] for r in valid_results]
        return (float(np.median(starts)), float(np.median(ends)))
    
    # Drop：至少2个检测点确认
    drop_results = [
        rms_results.get('drop'), 
        perc_results.get('drop'), 
        flux_results.get('drop'),
        history_results.get('drop')
    ]
    drop_count = sum(1 for r in drop_results if r is not None)
    
    if drop_count >= 2:
        drop = merge_time_range(drop_results, (duration * 0.35 - 2.0, duration * 0.35 + 2.0))
        drop_confidence = min(0.98, 0.6 + drop_count * 0.1)
    else:
        # 如果只有 Energy History 检测到（通常在极简氛围或复杂节奏中），作为备用
        if history_results.get('drop'):
            drop = history_results['drop']
            drop_confidence = 0.6
        else:
            drop = (duration * 0.35 - 2.0, duration * 0.35 + 2.0)
            drop_confidence = 0.5

def _get_default_structure(duration: float) -> Dict:
    """返回默认结构（当检测失败时）"""
    return {
        'structure': {
            'intro': (0.0, duration * 0.15),
            'chorus': (duration * 0.35 - 2.0, duration * 0.35 + 2.0),
            'breakdown': None,
            'build_up': None,
            'outro': (duration * 0.8, duration)
        },
        'confidence': 0.5,
        'drop_confidence': 0.5,
        'breakdown_confidence': 0.3,
        'build_up_confidence': 0.3,
        'intro_confidence': 0.6,
        'outro_confidence': 0.6
    }


def get_first_drop_time(structure: Dict) -> Optional[float]:
    """从结构信息中提取第一个Drop/Chorus时间"""
    drop_range = structure.get('structure', {}).get('chorus')
    if drop_range:
        return drop_range[0]  # 返回Drop/Chorus开始时间
    return None


def get_intro_end_time(structure: Dict) -> Optional[float]:
    """从结构信息中提取Intro结束时间"""
    intro_range = structure.get('structure', {}).get('intro')
    if intro_range:
        return intro_range[1]  # 返回Intro结束时间
    return None


def get_outro_start_time(structure: Dict) -> Optional[float]:
    """从结构信息中提取Outro开始时间"""
    outro_range = structure.get('structure', {}).get('outro')
    if outro_range:
        return outro_range[0]  # 返回Outro开始时间
    return None


