#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Set Completeness Skill
Calculates a 0-100 score based on DJ standards:
1. Harmonic Continuity (25%)
2. BPM Momentum stability (25%)
3. Phrase Alignment Success (25%)
4. Vocal Safety (No clashes) (25%)

V7.0 Guardrails:
- Boutique Hard Rejection: BPM > 8, Key Score < 90.
- Junk Drawer Filtering: Score < 40 filtered to [MISFIT] category.
"""

import statistics
from typing import List, Dict, Tuple

def calculate_set_completeness(tracks: List[Dict], transitions: List[Dict] = None) -> Dict:
    """
    计算 Set 的专业完整度评分 (0-100)
    """
    if not tracks or len(tracks) < 2:
        return {"total_score": 0, "breakdown": {}}

    # 1. Harmonic Flow Score (25%)
    harmonic_matches = 0
    total_transitions = len(tracks) - 1
    
    # 2. BPM Momentum Score (25%)
    bpm_jumps = 0
    
    # 3. Phrase Alignment Score (25%) 
    phrase_aligned = 0
    
    # 4. Vocal Safety Score (25%)
    vocal_clashes = 0

    # 如果没有传入 transitions，我们简单通过相邻轨道计算
    if not transitions:
        # 简单模拟转换数据
        pass

    # 实际统计数据
    harmonic_scores = []
    bpm_diffs = []
    
    for i in range(total_transitions):
        curr = tracks[i]
        nxt = tracks[i+1]
        
        # Harmonic
        h_score = curr.get('key_compatibility', 50) # 这个字段需要在排序时存入
        harmonic_scores.append(h_score)
        
        # BPM
        b_diff = abs(curr.get('bpm', 0) - nxt.get('bpm', 0))
        bpm_diffs.append(b_diff)
        
        # Phrase Alignment Detection (V9.2 Core)
        # 只要存在专业标点且不是 fallback 生成的，就认为是 Phrase 对齐成功的证据
        pro_hcs = curr.get('pro_hotcues', {})
        is_aligned = False
        if pro_hcs:
            # 检查 B 或 C 点是否带有 Rekordbox 标签
            b_label = pro_hcs.get('B', {}).get('PhraseLabel', '')
            c_label = pro_hcs.get('C', {}).get('PhraseLabel', '')
            if "[Rekordbox" in b_label or "[Rekordbox" in c_label:
                is_aligned = True
            elif "[Expert Advice]" in b_label or "[Expert Advice]" in c_label:
                is_aligned = True
                
        if is_aligned or curr.get('phrase_aligned', False):
            phrase_aligned += 1
            
        # Vocal Clash
        if nxt.get('vocal_clash_penalty', 0) > 0:
            vocal_clashes += 1

    # 计算各项子分
    # Harmonic: 平均分直接映射
    s_harmonic = sum(harmonic_scores) / total_transitions / 4 if total_transitions > 0 else 0
    
    # BPM: 跨度超过 8 BPM 扣分
    bad_bpm = sum(1 for d in bpm_diffs if d > 8)
    s_bpm = max(0, 25 - (bad_bpm * 5))
    
    # Phrase: 比例映射
    s_phrase = (phrase_aligned / total_transitions * 25) if total_transitions > 0 else 0
    
    # Vocal: 一个冲突扣 10 分，扣完为止
    s_vocal = max(0, 25 - (vocal_clashes * 10))

    total = s_harmonic + s_bpm + s_phrase + s_vocal
    
    return {
        "total_score": round(total, 1),
        "breakdown": {
            "harmonic_flow": round(s_harmonic, 1),
            "bpm_stability": round(s_bpm, 1),
            "phrase_alignment": round(s_phrase, 1),
            "vocal_safety": round(s_vocal, 1)
        },
        "rating": "Professional" if total > 85 else "Standard" if total > 70 else "Needs Improvement"
    }

def get_energy_curve_summary(tracks: List[Dict]) -> str:
    """分析能量变化曲线"""
    energies = [t.get('energy', 50) for t in tracks]
    if not energies: return "No data"
    
    start_e = sum(energies[:3]) / min(3, len(energies))
    end_e = sum(energies[-3:]) / min(3, len(energies))
    max_e = max(energies)
    max_idx = energies.index(max_e)
    
    if max_idx > len(energies) * 0.6 and end_e < max_e:
        return "Classic Arc (Warm-up -> Peak -> Outro)"
    elif end_e > start_e + 20:
        return "Ascending Tension (Club Style)"
    else:
        return "Variable Vibe"
