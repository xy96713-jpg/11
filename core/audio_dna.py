#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core: Audio DNA Mapping (V11.0)
================================
Centralized logic for mapping raw analysis data to high-level musical dimensions.
Used by Mashup Intelligence, Aesthetic Curator, and Set Sorter.
"""

from typing import Dict, List, Tuple, Optional

def map_dna_features(analysis: Dict) -> Dict:
    """[V11.0] 将缓存中的低级音频特征映射到标准化的 DNA 维度"""
    dna = analysis.copy()
    
    # 1. 音色 DNA (Timbre) - 基于 MFCC
    mfcc = analysis.get('energy_profile', {}).get('mfcc_mean', [])
    if mfcc and len(mfcc) >= 13:
        dna['timbre_low'] = max(0, min(1, (mfcc[0] + 100) / 200)) # 基频能量
        dna['timbre_mid'] = max(0, min(1, (mfcc[1] + 50) / 100))  # 中频特征
        dna['timbre_high'] = max(0, min(1, (mfcc[2] + 50) / 100)) # 高频特征
    else:
        # 降级处理
        dna['timbre_low'] = analysis.get('tonal_balance_low', 0.5)
        dna['timbre_mid'] = analysis.get('tonal_balance_mid', 0.3)
        dna['timbre_high'] = analysis.get('tonal_balance_high', 0.2)
        
    # 2. 律动 DNA (Groove) - 基于打击比例和起始点
    ep = analysis.get('energy_profile', {})
    p_ratio = ep.get('percussive_ratio', 0.5)
    o_density = ep.get('onset_global', 0.5)
    
    dna['swing_dna'] = p_ratio  # 律动刚性/表现力
    dna['groove_density'] = o_density
    dna['rhythmic_complexity'] = min(1.0, o_density * 5)
    
    # 3. 情感与氛围 (Vibe/Emotion)
    dna['stability'] = 1.0 - min(1.0, ep.get('energy_variance', 0.0) * 100)
    dna['valence'] = analysis.get('valence_window_mean', analysis.get('valence', 0.5))
    dna['arousal'] = analysis.get('arousal_window_mean', analysis.get('arousal', 0.5))
    
    # 4. 置信度审计 (Confidence)
    dna['data_confidence'] = (
        analysis.get('bpm_confidence', 1.0) * 
        analysis.get('key_confidence', 1.0) * 
        analysis.get('beat_stability', 1.0)
    )
    
    return dna

def calculate_dna_affinity(dna1: Dict, dna2: Dict) -> Tuple[float, List[str]]:
    """计算两个 DNA 之间的亲和力得分 (0-100)"""
    score = 0.0
    tags = []
    
    # A. 音色亲和力 (Timbre Sync) - 25分
    t1 = [dna1.get('timbre_low', 0.5), dna1.get('timbre_mid', 0.3), dna1.get('timbre_high', 0.2)]
    t2 = [dna2.get('timbre_low', 0.5), dna2.get('timbre_mid', 0.3), dna2.get('timbre_high', 0.2)]
    timbre_dist = sum((a - b)**2 for a, b in zip(t1, t2))**0.5
    timbre_match = max(0, 1.0 - timbre_dist * 2.0)
    score += timbre_match * 25
    if timbre_match > 0.8: tags.append("Timbre Twin")
    
    # B. 律动亲和力 (Groove Sync) - 25分
    g_match = max(0, 1.0 - abs(dna1.get('swing_dna', 0.5) - dna2.get('swing_dna', 0.5)))
    score += g_match * 25
    if g_match > 0.9: tags.append("Groove Locked")
    
    # C. 情感轨迹 (Emotional Alignment) - 30分
    e_dist = ((dna1.get('valence', 0.5) - dna2.get('valence', 0.5))**2 + 
              (dna1.get('arousal', 0.5) - dna2.get('arousal', 0.5))**2)**0.5
    if e_dist < 0.15:
        score += 30
        tags.append("Emotional Mirroring")
    elif e_dist < 0.4:
        score += 15
        tags.append("Mood Compatible")
    else:
        score -= 10 # 情绪冲突
        tags.append("Mood Clash")
        
    # D. 结构潜力 (Structural Sync) - 20分
    # 简化的结构匹配
    pm1 = dna1.get('phrase_markers', {}).get('bars_32', [])
    pm2 = dna2.get('phrase_markers', {}).get('bars_32', [])
    if pm1 and pm2:
        score += 20
        tags.append("Phrase Aligned")
        
    return max(0.0, score), tags
