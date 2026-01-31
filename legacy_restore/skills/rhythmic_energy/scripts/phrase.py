#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phrase对齐检测
Phrase Alignment Detection

根据 dj_rules.yaml 的 phrase_bars 配置，
确保Mix Point落在16拍（或32拍）的Phrase边界上。

专业DJ规则：
- 混音点应该在Phrase边界上（通常16拍或32拍）
- 避免在Verse/Chorus中间混音，破坏音乐结构
"""

from typing import Dict, Optional, Tuple


def calculate_phrase_position(
    mix_point_seconds: float,
    bpm: float,
    phrase_bars: int = 16
) -> Tuple[float, int, str]:
    """
    计算Mix Point在Phrase中的位置
    
    Args:
        mix_point_seconds: 混音点时间（秒）
        bpm: 歌曲BPM
        phrase_bars: Phrase长度（拍数，默认16拍）
        
    Returns:
        (position_in_phrase, phrase_number, alignment_status)
        - position_in_phrase: 在当前Phrase中的位置（0-1）
        - phrase_number: 当前是第几个Phrase
        - alignment_status: 对齐状态描述
    """
    if bpm <= 0:
        return (0.5, 0, "BPM无效")
    
    # 计算每拍时长（秒）
    beat_duration = 60.0 / bpm
    
    # 计算每Phrase时长（秒）
    phrase_duration = beat_duration * phrase_bars
    
    # 计算当前在第几个Phrase
    phrase_number = int(mix_point_seconds / phrase_duration)
    
    # 计算在当前Phrase中的位置（0-1）
    position_in_phrase = (mix_point_seconds % phrase_duration) / phrase_duration
    
    # 判断对齐状态
    # 0-0.1 或 0.9-1.0 视为"在边界附近"
    if position_in_phrase <= 0.1 or position_in_phrase >= 0.9:
        alignment_status = "✓ 在Phrase边界 (最佳)"
    elif position_in_phrase <= 0.25 or position_in_phrase >= 0.75:
        alignment_status = "◎ 接近Phrase边界 (可接受)"
    elif 0.4 <= position_in_phrase <= 0.6:
        alignment_status = "⚠ 在Phrase中间 (不推荐)"
    else:
        alignment_status = "△ 偏离Phrase边界"
    
    return (position_in_phrase, phrase_number, alignment_status)


def check_phrase_alignment(
    track: Dict,
    mix_point: float,
    dj_rules: Dict = None
) -> Tuple[float, str]:
    """
    检查Mix Point的Phrase对齐情况
    
    Args:
        track: 歌曲数据
        mix_point: 混音点时间（秒）
        dj_rules: dj_rules.yaml 配置字典
        
    Returns:
        (penalty_score, reason): 惩罚分数和原因
    """
    if not dj_rules:
        dj_rules = {}
    
    # 从配置读取Phrase参数
    phrase_bars = dj_rules.get('phrase_bars', 16)
    penalty_cap = dj_rules.get('phrase_penalty_cap', 0.55)
    threshold = dj_rules.get('phrase_dist_beats_threshold', 1.2)
    
    # 获取BPM
    bpm = track.get('bpm', 0)
    if not bpm or bpm <= 0:
        return (0.0, "无法检测：缺少BPM数据")
    
    # 计算Phrase位置
    position, phrase_num, status = calculate_phrase_position(
        mix_point, bpm, phrase_bars
    )
    
    # 计算惩罚
    # 在中间位置（0.4-0.6）惩罚最大
    if position <= 0.1 or position >= 0.9:
        penalty = 0.0
    elif position <= 0.25 or position >= 0.75:
        penalty = 0.1
    elif 0.4 <= position <= 0.6:
        penalty = min(penalty_cap, 0.4)
    else:
        penalty = 0.2
    
    return (penalty, f"{status} (Phrase#{phrase_num}, 位置{position:.1%})")


def suggest_better_phrase_aligned_point(
    track: Dict,
    current_mix_point: float,
    dj_rules: Dict = None,
    search_range_seconds: float = 15.0
) -> Tuple[float, str]:
    """
    建议更好的Phrase对齐混音点
    
    Args:
        track: 歌曲数据
        current_mix_point: 当前混音点
        dj_rules: 配置字典
        search_range_seconds: 搜索范围（秒）
        
    Returns:
        (suggested_point, reason)
    """
    if not dj_rules:
        dj_rules = {}
    
    bpm = track.get('bpm', 0)
    if not bpm or bpm <= 0:
        return (current_mix_point, "无法优化：缺少BPM")
    
    phrase_bars = dj_rules.get('phrase_bars', 16)
    beat_duration = 60.0 / bpm
    phrase_duration = beat_duration * phrase_bars
    
    # 找到最近的Phrase边界
    current_phrase = current_mix_point / phrase_duration
    prev_boundary = int(current_phrase) * phrase_duration
    next_boundary = (int(current_phrase) + 1) * phrase_duration
    
    # 选择更近的边界
    if abs(current_mix_point - prev_boundary) <= abs(next_boundary - current_mix_point):
        suggested = prev_boundary
    else:
        suggested = next_boundary
    
    # 确保在搜索范围内
    if abs(suggested - current_mix_point) > search_range_seconds:
        return (current_mix_point, f"最近边界超出搜索范围 ({abs(suggested - current_mix_point):.1f}秒)")
    
    # 确保不小于0
    if suggested < 5.0:
        suggested = next_boundary
    
    return (suggested, f"✓ 调整到Phrase边界 ({suggested:.1f}秒, 偏移{suggested - current_mix_point:+.1f}秒)")


# 能量曲线强制约束
ENERGY_PHASES = {
    "Warm-up": {"min": 30, "max": 55, "description": "暖场"},
    "Build-up": {"min": 50, "max": 70, "description": "递进"},
    "Peak": {"min": 65, "max": 90, "description": "高潮"},
    "Cool-down": {"min": 40, "max": 75, "description": "收尾"}
}


def validate_energy_curve(tracks: list, dj_rules: Dict = None) -> Tuple[bool, list]:
    """
    验证Set的能量曲线是否符合专业标准
    
    Args:
        tracks: 歌曲列表
        dj_rules: 配置字典
        
    Returns:
        (is_valid, issues): 是否有效和问题列表
    """
    if not tracks:
        return (True, [])
    
    issues = []
    n = len(tracks)
    
    # 将Set分成4个阶段
    warm_up_end = n // 5          # 前20%
    build_up_end = 2 * n // 5     # 20-40%
    peak_end = 4 * n // 5         # 40-80%
    # cool_down: 80-100%
    
    phases = [
        ("Warm-up", 0, warm_up_end),
        ("Build-up", warm_up_end, build_up_end),
        ("Peak", build_up_end, peak_end),
        ("Cool-down", peak_end, n)
    ]
    
    for phase_name, start, end in phases:
        phase_config = ENERGY_PHASES.get(phase_name, {})
        min_energy = phase_config.get("min", 0)
        max_energy = phase_config.get("max", 100)
        
        for i in range(start, end):
            if i >= len(tracks):
                break
            track = tracks[i]
            energy = track.get('energy', 50)
            
            if energy < min_energy:
                issues.append({
                    "track_idx": i,
                    "title": track.get('title', 'Unknown'),
                    "phase": phase_name,
                    "issue": f"能量过低 ({energy} < {min_energy})",
                    "severity": "warning"
                })
            elif energy > max_energy:
                issues.append({
                    "track_idx": i,
                    "title": track.get('title', 'Unknown'),
                    "phase": phase_name,
                    "issue": f"能量过高 ({energy} > {max_energy})",
                    "severity": "warning"
                })
    
    is_valid = len([i for i in issues if i.get('severity') == 'error']) == 0
    
    return (is_valid, issues)


def suggest_energy_reorder(tracks: list) -> list:
    """
    建议能量曲线重排序
    
    基于专业能量曲线：Warm-up → Build-up → Peak → Cool-down
    """
    if not tracks or len(tracks) < 4:
        return tracks
    
    # 按能量排序
    sorted_tracks = sorted(tracks, key=lambda t: t.get('energy', 50))
    
    n = len(sorted_tracks)
    
    # 低能量 → Warm-up
    warm_up = sorted_tracks[:n//5]
    
    # 中低能量 → Build-up
    build_up = sorted_tracks[n//5:2*n//5]
    
    # 高能量 → Peak
    peak = sorted_tracks[3*n//5:]
    
    # 中等能量 → Cool-down
    cool_down = sorted_tracks[2*n//5:3*n//5]
    
    # 组合：Warm-up(升序) → Build-up(升序) → Peak(升序后降序) → Cool-down(降序)
    result = []
    result.extend(sorted(warm_up, key=lambda t: t.get('energy', 50)))
    result.extend(sorted(build_up, key=lambda t: t.get('energy', 50)))
    # Peak: 先升后降
    peak_sorted = sorted(peak, key=lambda t: t.get('energy', 50))
    mid = len(peak_sorted) // 2
    result.extend(peak_sorted[:mid])
    result.extend(reversed(peak_sorted[mid:]))
    result.extend(sorted(cool_down, key=lambda t: t.get('energy', 50), reverse=True))
    
    return result
