#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPM渐进式管理
BPM Progressive Management

确保BPM在能量阶段内遵循渐进规则：
- Warm-up/Build-up: BPM逐步上升
- Peak: 允许小幅波动（±5 BPM）
- Cool-down: BPM逐步下降
"""

from typing import Dict, List, Tuple


def validate_bpm_progression(
    tracks: List[Dict],
    dj_rules: Dict = None
) -> Tuple[bool, List[Dict]]:
    """
    验证Set的BPM渐进是否符合专业标准
    
    Args:
        tracks: 歌曲列表
        dj_rules: dj_rules.yaml 配置字典
        
    Returns:
        (is_valid, issues): 是否有效和问题列表
    """
    if not tracks or len(tracks) < 2:
        return (True, [])
    
    if not dj_rules:
        dj_rules = {}
    
    issues = []
    n = len(tracks)
    
    # 能量阶段划分
    warm_up_end = n // 5          # 前20%
    build_up_end = 2 * n // 5     # 20-40%
    peak_end = 4 * n // 5         # 40-80%
    
    # BPM容差
    bpm_tolerance = dj_rules.get('bpm', {}).get('direct_tolerance', 15.0)
    peak_tolerance = 5.0  # Peak阶段允许±5 BPM波动
    
    for i in range(1, n):
        prev_bpm = tracks[i-1].get('bpm', 0)
        curr_bpm = tracks[i].get('bpm', 0)
        
        if not prev_bpm or not curr_bpm:
            continue
        
        bpm_diff = curr_bpm - prev_bpm  # 正值=加速，负值=减速
        
        # 判断当前阶段
        if i < warm_up_end:
            phase = "Warm-up"
            # Warm-up应该加速或保持
            if bpm_diff < -bpm_tolerance:
                issues.append({
                    "track_idx": i,
                    "title": tracks[i].get('title', 'Unknown'),
                    "phase": phase,
                    "issue": f"BPM异常减速 ({prev_bpm:.0f} → {curr_bpm:.0f}, Δ{bpm_diff:+.0f})",
                    "severity": "warning"
                })
        
        elif i < build_up_end:
            phase = "Build-up"
            # Build-up应该加速
            if bpm_diff < -bpm_tolerance:
                issues.append({
                    "track_idx": i,
                    "title": tracks[i].get('title', 'Unknown'),
                    "phase": phase,
                    "issue": f"BPM异常减速 ({prev_bpm:.0f} → {curr_bpm:.0f}, Δ{bpm_diff:+.0f})",
                    "severity": "warning"
                })
        
        elif i < peak_end:
            phase = "Peak"
            # Peak允许小幅波动
            if abs(bpm_diff) > bpm_tolerance:
                issues.append({
                    "track_idx": i,
                    "title": tracks[i].get('title', 'Unknown'),
                    "phase": phase,
                    "issue": f"BPM跳跃过大 ({prev_bpm:.0f} → {curr_bpm:.0f}, Δ{bpm_diff:+.0f})",
                    "severity": "warning"
                })
        
        else:
            phase = "Cool-down"
            # Cool-down应该减速或保持
            if bpm_diff > bpm_tolerance:
                issues.append({
                    "track_idx": i,
                    "title": tracks[i].get('title', 'Unknown'),
                    "phase": phase,
                    "issue": f"BPM异常加速 ({prev_bpm:.0f} → {curr_bpm:.0f}, Δ{bpm_diff:+.0f})",
                    "severity": "warning"
                })
    
    is_valid = len([i for i in issues if i.get('severity') == 'error']) == 0
    return (is_valid, issues)


def suggest_bpm_reorder(
    tracks: List[Dict],
    phase: str = "auto"
) -> List[Dict]:
    """
    基于BPM渐进规则重新排序
    
    Args:
        tracks: 歌曲列表
        phase: 能量阶段 ("warm_up", "build_up", "peak", "cool_down", "auto")
        
    Returns:
        重新排序后的歌曲列表
    """
    if not tracks or len(tracks) < 2:
        return tracks
    
    if phase == "warm_up" or phase == "build_up":
        # 升序排列
        return sorted(tracks, key=lambda t: t.get('bpm', 0))
    
    elif phase == "cool_down":
        # 降序排列
        return sorted(tracks, key=lambda t: t.get('bpm', 0), reverse=True)
    
    elif phase == "peak":
        # 波浪形：先升后降
        sorted_tracks = sorted(tracks, key=lambda t: t.get('bpm', 0))
        mid = len(sorted_tracks) // 2
        return sorted_tracks[:mid] + list(reversed(sorted_tracks[mid:]))
    
    else:  # auto
        # 自动分段处理
        n = len(tracks)
        warm_up = tracks[:n//5]
        build_up = tracks[n//5:2*n//5]
        peak = tracks[2*n//5:4*n//5]
        cool_down = tracks[4*n//5:]
        
        result = []
        result.extend(suggest_bpm_reorder(warm_up, "warm_up"))
        result.extend(suggest_bpm_reorder(build_up, "build_up"))
        result.extend(suggest_bpm_reorder(peak, "peak"))
        result.extend(suggest_bpm_reorder(cool_down, "cool_down"))
        
        return result


def get_bpm_curve_summary(tracks: List[Dict]) -> Dict:
    """
    获取BPM曲线摘要
    
    Returns:
        {
            "min_bpm": float,
            "max_bpm": float,
            "avg_bpm": float,
            "trend": str ("ascending", "descending", "wave", "flat")
        }
    """
    if not tracks:
        return {"min_bpm": 0, "max_bpm": 0, "avg_bpm": 0, "trend": "unknown"}
    
    bpms = [t.get('bpm', 0) for t in tracks if t.get('bpm', 0) > 0]
    
    if not bpms:
        return {"min_bpm": 0, "max_bpm": 0, "avg_bpm": 0, "trend": "unknown"}
    
    min_bpm = min(bpms)
    max_bpm = max(bpms)
    avg_bpm = sum(bpms) / len(bpms)
    
    # 判断趋势
    if len(bpms) < 2:
        trend = "flat"
    else:
        first_quarter_avg = sum(bpms[:len(bpms)//4]) / max(1, len(bpms)//4)
        last_quarter_avg = sum(bpms[-len(bpms)//4:]) / max(1, len(bpms)//4)
        mid_avg = sum(bpms[len(bpms)//4:-len(bpms)//4]) / max(1, len(bpms) - 2*(len(bpms)//4))
        
        if last_quarter_avg > first_quarter_avg + 5:
            trend = "ascending"
        elif first_quarter_avg > last_quarter_avg + 5:
            trend = "descending"
        elif mid_avg > first_quarter_avg and mid_avg > last_quarter_avg:
            trend = "wave"
        else:
            trend = "flat"
    
    return {
        "min_bpm": min_bpm,
        "max_bpm": max_bpm,
        "avg_bpm": avg_bpm,
        "trend": trend
    }
