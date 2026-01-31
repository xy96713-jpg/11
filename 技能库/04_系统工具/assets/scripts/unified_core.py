#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Expert Core (V8.0)
==========================
专家系统核心大脑，整合了之前分散在各个 SKill 中的核心算法。
目标：逻辑统一、规则统一、标准统一。

组件：
1. VocalConflictEngine: 智能人声/副歌冲突检测
2. PhraseQuantizer: 动态乐句量化引擎
3. CueStandard: 标点命名与色彩标准定义
"""

from typing import Dict, List, Tuple, Optional, Union
import math

class CueStandard:
    """标点命名与色彩标准定义 (V6.0 Standard)"""
    
    # 色彩常数
    COLOR_BLUE = "0x0000FF"    # 过渡/结构 (Intro/Outro)
    COLOR_RED = "0xFF0000"     # 能量爆发 (Drop/Chorus)
    COLOR_GREEN = "0x00FF00"   # 创意/混搭 (Mashup/Bridge)
    COLOR_YELLOW = "0xFFFF00"  # 平稳段落 (Verse)
    COLOR_CYAN = "0x00FFFF"    # 氛围/填充
    COLOR_MAGENTA = "0xFF00FF" # 特殊点
    
    # 标准标签映射
    MAP_V6 = {
        'A': {'Name': '[IN] START', 'Color': COLOR_BLUE, 'Kind': 1},
        'B': {'Name': '[IN] ENERGY', 'Color': COLOR_YELLOW, 'Kind': 2},
        'C': {'Name': '[OUT] START', 'Color': COLOR_BLUE, 'Kind': 3},
        'D': {'Name': '[OUT] END', 'Color': COLOR_BLUE, 'Kind': 4},
        'E': {'Name': '[DROP]', 'Color': COLOR_RED, 'Kind': 5},
        'F': {'Name': '[DROP] 2', 'Color': COLOR_RED, 'Kind': 5},
        'G': {'Name': '[BRIDGE]', 'Color': COLOR_CYAN, 'Kind': 6},
        'H': {'Name': '[LOOP] EMERGENCY', 'Color': COLOR_MAGENTA, 'Kind': 8}
    }

    @staticmethod
    def get_standard_cue(char_key: str) -> Dict:
        """获取标准标点模板"""
        return CueStandard.MAP_V6.get(char_key, {})

class PhraseQuantizer:
    """动态乐句量化引擎"""
    
    @staticmethod
    def bars_to_seconds(bars: float, bpm: float) -> float:
        """标准换算：Bars -> Seconds"""
        if bpm <= 0: return 0.0
        return bars * 4 * (60.0 / bpm)
        
    @staticmethod
    def quantize(
        timestamp: float, 
        bpm: float, 
        anchor: float = 0.0, 
        dj_rules: Dict = None,
        force_snap_bars: Optional[int] = None
    ) -> float:
        """
        全功能量化函数
        
        Args:
            timestamp: 原始时间点
            bpm: 歌曲 BPM
            anchor: 物理锚点 (Inizio)
            dj_rules: 配置字典 (用于通过 phrase_bars 计算 snap)
            force_snap_bars: 强制指定的量化步长 (bars)，若为 None 则自动计算
        """
        if bpm <= 0: return timestamp
        
        # 1. 确定量化步长 (Snap Interval)
        snap_bars = 0
        
        if force_snap_bars is not None:
            snap_bars = force_snap_bars
        elif dj_rules:
            # 自动逻辑：phrase_bars 的一半，或者至少 8 bars
            p_bars = dj_rules.get('phrase_bars', 16)
            snap_bars = int(p_bars / 2) if p_bars >= 16 else 8
        
        # 2. 执行量化
        beat_dur = 60.0 / bpm
        
        # 计算相对拍数
        beats_from_anchor = (timestamp - anchor) / beat_dur
        
        # 基础拍子对齐 (Grid Alignment)
        quantized_beats = round(beats_from_anchor)
        
        # 乐句对齐 (Phrase Snapping)
        if snap_bars > 0:
            beats_per_snap = snap_bars * 4
            quantized_beats = round(quantized_beats / beats_per_snap) * beats_per_snap
            
        # 还原时间
        return max(0.0, anchor + (quantized_beats * beat_dur))

class VocalConflictEngine:
    """人声冲突检测引擎"""
    
    @staticmethod
    def normalize_region(region) -> Tuple[float, float]:
        """归一化区域格式：支持 list, tuple, dict"""
        if isinstance(region, (list, tuple)):
            return region[0], region[1] if len(region) > 1 else region[0]
        elif isinstance(region, dict):
            return region.get('start', 0.0), region.get('end', 0.0)
        return 0.0, 0.0

    @staticmethod
    def is_active(timestamp: float, regions: List, buffer: float = 0.5) -> bool:
        """检查某时刻是否有人声"""
        for r in regions:
            s, e = VocalConflictEngine.normalize_region(r)
            if s - buffer <= timestamp <= e + buffer:
                return True
        return False
        
    @staticmethod
    def check_conflict(
        track_a: Dict, 
        track_b: Dict, 
        mix_out: float, 
        mix_in: float, 
        dj_rules: Dict
    ) -> Tuple[float, str]:
        """
        完整的冲突检测逻辑 (移植自 skill_vocal_aware_cues)
        """
        if not dj_rules.get('enable_vocal_timeline_check', False):
            return 0.0, "未启用检测"

        vocal_weight = dj_rules.get('vocal_overlap_weight', 20.0)
        chorus_weight = dj_rules.get('chorus_overlap_penalty', 15.0)
        
        # 获取数据
        va = track_a.get('vocals', {}) or {}
        vb = track_b.get('vocals', {}) or {}
        
        # 1. 人声段检测
        a_active = VocalConflictEngine.is_active(mix_out, va.get('segments', []))
        b_active = VocalConflictEngine.is_active(mix_in, vb.get('segments', []))
        
        if a_active and b_active:
            penalty = min(vocal_weight / 100.0, 0.9)
            return penalty, "人声冲突 (Vocal Clash)"
            
        # 2. 副歌段检测 (更严重)
        if dj_rules.get('enable_chorus_overlap_check', True):
            a_chorus = VocalConflictEngine.is_active(mix_out, va.get('chorus', []))
            b_chorus = VocalConflictEngine.is_active(mix_in, vb.get('chorus', []))
            
            if a_chorus and b_chorus:
                penalty = min(chorus_weight / 100.0, 0.9)
                return penalty, "副歌冲突 (Chorus Clash)"
                
        return 0.0, "无冲突"
