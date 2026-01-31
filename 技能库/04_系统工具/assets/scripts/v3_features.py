#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill: Mashup V3-PRO Features
- 频谱掩蔽（Spectral Masking）分析
- 律动摆（Swing DNA）指纹提取
- 能量曲线（Energy Curve）动态扫描
- 音质纹理（Timbre Texture）特征聚类
- 氛围与深度标签（Vibe & Deep Tags）分析
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

def calculate_spectral_bands(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    [最强大脑评分项] 计算四个核心频段的能量占比。
    用于预防频谱掩蔽（Spectral Masking）。
    """
    if not HAS_LIBROSA or y.size == 0:
        return {}
        
    # 计算功率谱
    S = np.abs(librosa.stft(y))**2
    freqs = librosa.fft_frequencies(sr=sr)
    total_power = np.sum(S) + 1e-10
    
    # 频段定义
    bands = {
        "sub_bass": (20, 150),
        "low_mid": (150, 500),
        "mid_range": (500, 2000),
        "high_presence": (2000, 8000)
    }
    
    ratios = {}
    for name, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs <= high)
        ratios[name] = float(np.sum(S[mask, :]) / total_power)
        
    return ratios

def calculate_swing_dna(beat_times: np.ndarray) -> float:
    """
    [最强大脑评分项] 计算律动摇摆感（Swing DNA）。
    基于连续 Beat 之间的间隔模式：(长-短-长-短)。
    """
    if len(beat_times) < 8:
        return 0.0
        
    intervals = np.diff(beat_times)
    # 取连续两个间隔的比例，接近 2:1 或 1.5:1 代表明显 Swing
    ratios = []
    for i in range(0, len(intervals) - 1, 2):
        r = intervals[i] / (intervals[i+1] + 1e-6)
        ratios.append(r)
        
    # 如果比例显著偏离 1.0 且具有一致性，则判定为 Swing
    avg_ratio = np.mean(ratios)
    stability = 1.0 - np.std(ratios)
    
    # 归一化结果 (0.0=完全直板, 1.0=极度摇摆)
    swing_score = np.clip(abs(avg_ratio - 1.0) * stability * 2.0, 0.0, 1.0)
    return float(swing_score)

def calculate_energy_curve(y: np.ndarray, sr: int, window_sec: float = 8.0) -> List[float]:
    """
    [最强大脑评分项] 生成能量斜率曲线。
    以 window_sec 为步长，计算全曲能量的动态走势。
    """
    if not HAS_LIBROSA or y.size == 0:
        return []
        
    # 计算 RMS
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    # 归一化
    rms = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
    
    # 降采样到 window_sec 级别的值
    samples_per_window = int(window_sec * sr / hop_length)
    if samples_per_window <= 0: return []
    
    curve = []
    for i in range(0, len(rms), samples_per_window):
        chunk = rms[i:i + samples_per_window]
        if len(chunk) > 0:
            curve.append(float(np.mean(chunk)))
    return curve

def calculate_timbre_texture(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    [最强大脑评分项] 分析音色质感（Timbre Texture）。
    使用 MFCC 的统计特征来区分“干净/温暖”与“粗糙/密集”。
    """
    if not HAS_LIBROSA or y.size == 0:
        return {}
        
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    # 系数 1 通常代表能量，2-13 代表音色形状
    # 使用标准差来代表“纹理复杂性”
    texture_complexity = np.mean(np.std(mfcc[1:], axis=1))
    
    # 归一化映射 (经验值：10-50 映射到 0-1)
    complexity_score = np.clip((texture_complexity - 10) / 40.0, 0.0, 1.0)
    
    return {
        "complexity": float(complexity_score),
        "metadata_texture": "rough" if complexity_score > 0.6 else "silky"
    }

def calculate_vibe_tags(y: np.ndarray, sr: int, energy: float = 0.5) -> Dict[str, any]:
    """
    [最强大脑评分项] 分析歌曲氛围与深度标签 (Vibe & Emotional Tags)。
    基于 Valence (通过大/小调及亮度估算) 与 Energy 的二维情感象限。
    """
    if not HAS_LIBROSA or y.size == 0:
        return {"tags": [], "emotional_quadrant": "Neutral"}

    # 1. 估算 Valence (情感正负)
    # 逻辑：亮度高 + 大调倾向 = 积极 Valence
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = np.mean(centroid) / (sr/2) # 归一化亮度
    
    # 色彩分析 (Chromagram) 辅助判断调性情感感
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    # 简化的“幸福感”估算：如果主要和弦包含较多协和音程
    valence = np.clip(brightness * 1.5, 0.0, 1.0) 
    
    # 2. 情感象限定义 (Russell's Circumplex Model)
    # Energy (Arousal) vs Valence
    tags = []
    if energy > 0.7:
        if valence > 0.5: quadrant, tag = "Happy/Excited", "High Energy / Party"
        else: quadrant, tag = "Angry/Aggressive", "Dark / Intense"
    elif energy < 0.3:
        if valence > 0.5: quadrant, tag = "Calm/Relaxed", "Chill / Dreamy"
        else: quadrant, tag = "Sad/Depressed", "Melancholy / Deep"
    else:
        quadrant, tag = "Neutral", "Balanced"
    
    tags.append(tag)
    
    # 3. 补充氛围标签 (基于音色和动态)
    rms = librosa.feature.rms(y=y)[0]
    dynamic_range = np.std(rms) / (np.mean(rms) + 1e-6)
    
    if dynamic_range > 0.5: tags.append("Dynamic")
    if brightness > 0.3: tags.append("Bright")
    else: tags.append("Warm / Muffled")
    
    return {
        "vibe_score": float(valence),
        "emotional_quadrant": quadrant,
        "deep_tags": tags
    }
