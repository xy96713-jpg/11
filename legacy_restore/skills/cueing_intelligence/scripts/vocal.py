#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人声感知混音点检测
Vocal-Aware Mix Point Detection

根据 dj_rules.yaml 的 vocal_overlap_weight 和 chorus_overlap_penalty 规则，
检测并惩罚人声-on-人声和副歌-on-副歌的混音点。

专业DJ规则：
- 避免在A曲的人声段混入B曲的人声段（混浊）
- 避免在A曲的副歌混入B曲的副歌（歌词冲突）
- 优先选择人声→器乐 或 器乐→人声的混音点
"""

from typing import Dict, Optional, Tuple, List

# 【V8.0】引入专家核心模块
try:
    from skills.unified_expert_core import VocalConflictEngine
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback (保持旧逻辑)


def check_vocal_overlap_at_mix_point(
    track_a: Dict,
    track_b: Dict,
    mix_out_time: float,
    mix_in_time: float,
    dj_rules: Dict = None
) -> Tuple[float, str]:
    """
    检查混音点是否存在人声冲突
    
    Args:
        track_a: 当前歌曲（Mix Out）
        track_b: 下一首歌曲（Mix In）
        mix_out_time: Track A 的混出点（秒）
        mix_in_time: Track B 的混入点（秒）
        dj_rules: dj_rules.yaml 配置字典
        
    Returns:
        (penalty_score, reason): 惩罚分数和原因
    """
    if CORE_AVAILABLE:
        return VocalConflictEngine.check_conflict(
            track_a=track_a, 
            track_b=track_b, 
            mix_out=mix_out_time, 
            mix_in=mix_in_time, 
            dj_rules=dj_rules
        )
    
    # === Legacy Fallback Implementation ===
    if not dj_rules:
        dj_rules = {}
    
    # 读取配置
    enabled = dj_rules.get('enable_vocal_timeline_check', False)
    if not enabled:
        return (0.0, "未启用人声时间轴检测")
    
    vocal_weight = dj_rules.get('vocal_overlap_weight', 20.0)
    chorus_weight = dj_rules.get('chorus_overlap_penalty', 15.0)
    penalty_cap = dj_rules.get('vocal_clash_penalty_cap', 0.9)
    
    # 获取人声时间轴数据
    vocals_a = track_a.get('vocals', {}) or {}
    vocals_b = track_b.get('vocals', {}) or {}
    
    # 如果缺少人声数据，跳过检测
    if not vocals_a or not vocals_b:
        return (0.0, "缺少人声数据")
    
    # 检查 Mix Out 点是否在 Track A 的人声段
    a_vocal_segments = vocals_a.get('segments', []) or []
    a_is_vocal_at_mixout = False
    
    # 辅助函数：归一化获取 start, end
    def _get_se(seg):
        if isinstance(seg, (list, tuple)): return seg[0], seg[1]
        if isinstance(seg, dict): return seg.get('start', 0), seg.get('end', 0)
        return 0, 0

    for seg in a_vocal_segments:
        start, end = _get_se(seg)
        if start <= mix_out_time <= end:
            a_is_vocal_at_mixout = True
            break
    
    # 检查 Mix In 点是否在 Track B 的人声段
    b_vocal_segments = vocals_b.get('segments', []) or []
    b_is_vocal_at_mixin = False
    for seg in b_vocal_segments:
        start, end = _get_se(seg)
        if start <= mix_in_time <= end:
            b_is_vocal_at_mixin = True
            break
    
    # 🚨 检测 1: 人声-on-人声冲突
    if a_is_vocal_at_mixout and b_is_vocal_at_mixin:
        penalty = min(vocal_weight / 100.0, penalty_cap)
        return (penalty, f"人声-on-人声冲突: MixOut@{mix_out_time:.1f}s 和 MixIn@{mix_in_time:.1f}s 都在人声段")
    
    # 🚨 检测 2: 副歌-on-副歌冲突（更严重）
    a_chorus_segments = vocals_a.get('chorus', []) or []
    b_chorus_segments = vocals_b.get('chorus', []) or []
    
    a_is_chorus_at_mixout = False
    for seg in a_chorus_segments:
        start, end = _get_se(seg)
        if start <= mix_out_time <= end:
            a_is_chorus_at_mixout = True
            break
    
    b_is_chorus_at_mixin = False
    for seg in b_chorus_segments:
        start, end = _get_se(seg)
        if start <= mix_in_time <= end:
            b_is_chorus_at_mixin = True
            break
    
    if a_is_chorus_at_mixout and b_is_chorus_at_mixin:
        penalty = min(chorus_weight / 100.0, penalty_cap)
        return (penalty, f"副歌-on-副歌冲突: MixOut@{mix_out_time:.1f}s 和 MixIn@{mix_in_time:.1f}s 都在副歌段")
    
    # ✅ 无冲突
    if a_is_vocal_at_mixout and not b_is_vocal_at_mixin:
        return (0.0, "✓ 人声→器乐 (推荐)")
    elif not a_is_vocal_at_mixout and b_is_vocal_at_mixin:
        return (0.0, "✓ 器乐→人声 (推荐)")
    else:
        return (0.0, "✓ 器乐→器乐 (最佳)")


def calculate_vocal_alerts(
    vocal_regions: List[Tuple[float, float]],
    bpm: float,
    duration: float,
    settings: Dict = None
) -> Dict:
    """
    计算人声预警 HotCue 点 (E/F/G/H)
    
    Args:
        vocal_regions: [(start, end), ...] 人声段列表
        bpm: 歌曲BPM
        duration: 歌曲总时长
        settings: 配置项
        
    Returns:
        Dict 包含 E, F, G, H 的 HotCue 信息
    """
    if not vocal_regions or bpm <= 0:
        return {}
        
    res = {}
    
    # 过滤掉极短的人声段
    # 过滤掉极短的人声段
    # 兼容处理
    def _parse_region(r):
        if CORE_AVAILABLE:
            return VocalConflictEngine.normalize_region(r)
        
        if isinstance(r, (list, tuple)): return r[0], r[1]
        if isinstance(r, dict): return r.get('start', 0), r.get('end', 0)
        return 0, 0
        
    normalized_regions = [_parse_region(r) for r in vocal_regions]
    valid_regions = [r for r in normalized_regions if r[1] - r[0] > 2.0]
    if not valid_regions:
        return {}
        
    # E (4): 第一段 Verse Start (第一个人声开始)
    first_vocal = valid_regions[0]
    res['E'] = {
        'Name': 'E: Verse Start',
        'Start': first_vocal[0],
        'Num': 4,
        'Color': {'Red': 128, 'Green': 0, 'Blue': 255} # 紫色
    }
    
    # F (5): 可能是 Chorus Start (寻找时长较长且靠后的人声段)
    # 策略：取第2或第3个段，或者找最长的段
    if len(valid_regions) >= 2:
        # 寻找最长的那个作为 Chorus (G) 之前的 F
        longest_region = max(valid_regions, key=lambda r: r[1] - r[0])
        res['F'] = {
            'Name': 'F: Main Vocal / Chorus',
            'Start': longest_region[0],
            'Num': 5,
            'Color': {'Red': 0, 'Green': 0, 'Blue': 255} # 蓝色
        }
    
    # G (6): Breakdown Vocal 或 最后一个片段
    if len(valid_regions) >= 3:
        last_vocal = valid_regions[-1]
        res['G'] = {
            'Name': 'G: Final Vocal / Outro-Vocal',
            'Start': last_vocal[0],
            'Num': 6,
            'Color': {'Red': 255, 'Green': 0, 'Blue': 0} # 红色
        }
        
    return res


def get_recommended_mix_points_avoiding_vocals(
    track_a: Dict,
    track_b: Dict,
    dj_rules: Dict = None
) -> Tuple[Optional[float], Optional[float], str]:
    """
    推荐避免人声冲突的混音点
    
    Args:
        track_a: 当前歌曲
        track_b: 下一首歌曲
        dj_rules: dj_rules.yaml 配置字典
        
    Returns:
        (recommended_mix_out, recommended_mix_in, reason)
    """
    if not dj_rules:
        dj_rules = {}
    
    # 获取现有的混音点建议
    default_mix_out = track_a.get('mix_out_point') or track_a.get('recommended_mix_out')
    default_mix_in = track_b.get('mix_in_point') or track_b.get('recommended_mix_in')
    
    if not default_mix_out or not default_mix_in:
        return (default_mix_out, default_mix_in, "缺少默认混音点")
    
    # 检查默认混音点是否有人声冲突
    penalty, reason = check_vocal_overlap_at_mix_point(
        track_a, track_b, default_mix_out, default_mix_in, dj_rules
    )
    
    if penalty == 0.0:
        return (default_mix_out, default_mix_in, reason)
    
    # 如果有冲突，尝试寻找替代混音点
    # 策略：在默认点前后±15秒内寻找器乐段
    vocals_a = track_a.get('vocals', {}) or {}
    vocals_b = track_b.get('vocals', {}) or {}
        
    a_vocal_segments = vocals_a.get('segments', []) or []
    b_vocal_segments = vocals_b.get('segments', []) or []
    
    # 尝试向前或向后调整 Mix Out 点
    search_range = 15.0  # 搜索范围：±15秒
    step = 2.0  # 步长：每2秒检查一次
    
    best_mix_out = default_mix_out
    best_mix_in = default_mix_in
    best_penalty = penalty
    
    for delta in [d * step for d in range(-int(search_range/step), int(search_range/step) + 1)]:
        test_mix_out = default_mix_out + delta
        test_mix_in = default_mix_in + delta  # 保持混音窗口长度不变
        
        # 确保不超出曲目长度
        duration_a = track_a.get('duration', 300)
        duration_b = track_b.get('duration', 300)
        if test_mix_out < 10 or test_mix_out > duration_a - 10:
            continue
        if test_mix_in < 5 or test_mix_in > duration_b - 20:
            continue
        
        test_penalty, test_reason = check_vocal_overlap_at_mix_point(
            track_a, track_b, test_mix_out, test_mix_in, dj_rules
        )
        
        if test_penalty < best_penalty:
            best_mix_out = test_mix_out
            best_mix_in = test_mix_in
            best_penalty = test_penalty
            
            if best_penalty == 0.0:
                return (best_mix_out, best_mix_in, f"✓ 调整混音点避免人声冲突 (偏移{delta:+.1f}秒)")
    
    # 如果找不到完美的点，返回最佳的点
    if best_penalty < penalty:
        return (best_mix_out, best_mix_in, f"⚠ 部分缓解人声冲突 (惩罚{best_penalty:.2f})")
    
    # 实在找不到，只能保留原混音点并警告
    return (default_mix_out, default_mix_in, f"⚠ {reason} (无法找到替代点)")
