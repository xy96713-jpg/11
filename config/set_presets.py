#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set切分预设配置
支持不同场景（Club/Radio/Warm-up）的快速切换
"""

from typing import Dict

# 场景预设配置
SET_PRESETS = {
    "club": {
        "name": "Club Set",
        "description": "标准Club Set，适合夜店演出",
        "split": {
            "target_duration_minutes": 60.0,
            "min_songs": 25,
            "ideal_songs_min": 30,
            "ideal_songs_max": 50,
            "max_songs": 70,
            "max_duration": 120.0,
            "min_set_duration_force": 50.0,
            "bpm_segment_thresholds": [120, 140, 160],
            "use_bpm_segmentation": True,
            "energy_low_threshold": 40,
            "style_change_weight": 0.8,
        }
    },
    "radio": {
        "name": "Radio Set",
        "description": "电台Set，时长较短，歌曲较多",
        "split": {
            "target_duration_minutes": 45.0,
            "min_songs": 15,
            "ideal_songs_min": 20,
            "ideal_songs_max": 40,
            "max_songs": 50,
            "max_duration": 60.0,
            "min_set_duration_force": 30.0,
            "bpm_segment_thresholds": [110, 130, 150],
            "use_bpm_segmentation": True,
            "energy_low_threshold": 35,
            "style_change_weight": 0.6,
        }
    },
    "warm_up": {
        "name": "Warm-up Set",
        "description": "暖场Set，低能量，渐进式",
        "split": {
            "target_duration_minutes": 90.0,
            "min_songs": 30,
            "ideal_songs_min": 35,
            "ideal_songs_max": 55,
            "max_songs": 70,
            "max_duration": 150.0,
            "min_set_duration_force": 60.0,
            "bpm_segment_thresholds": [100, 120, 140],
            "use_bpm_segmentation": True,
            "energy_low_threshold": 30,
            "style_change_weight": 0.5,
        }
    },
    "extended": {
        "name": "Extended Set",
        "description": "超长Set，适合长时间演出",
        "split": {
            "target_duration_minutes": 120.0,
            "min_songs": 40,
            "ideal_songs_min": 50,
            "ideal_songs_max": 70,
            "max_songs": 90,
            "max_duration": 240.0,
            "min_set_duration_force": 90.0,
            "bpm_segment_thresholds": [110, 130, 150, 170],
            "use_bpm_segmentation": True,
            "energy_low_threshold": 40,
            "style_change_weight": 0.7,
        }
    },
    "default": {
        "name": "Default Set",
        "description": "默认配置",
        "split": {
            "target_duration_minutes": 90.0,
            "min_songs": 20,
            "ideal_songs_min": 30,
            "ideal_songs_max": 50,
            "max_songs": 60,
            "max_duration": 180.0,
            "min_set_duration_force": 50.0,
            "bpm_segment_thresholds": [110, 130, 150],
            "use_bpm_segmentation": True,
            "energy_low_threshold": 40,
            "style_change_weight": 0.7,
        }
    }
}


def get_preset(preset_name: str = "default") -> Dict:
    """
    获取预设配置
    
    Args:
        preset_name: 预设名称（club/radio/warm_up/extended/default）
        
    Returns:
        Dict: 预设配置字典
    """
    preset_name = preset_name.lower()
    if preset_name not in SET_PRESETS:
        preset_name = "default"
    
    return SET_PRESETS[preset_name]


def list_presets() -> Dict[str, Dict]:
    """
    列出所有可用的预设
    
    Returns:
        Dict[str, Dict]: 所有预设的字典
    """
    return SET_PRESETS


def apply_preset_to_config(base_config: Dict, preset_name: str = "default") -> Dict:
    """
    将预设配置应用到基础配置
    
    Args:
        base_config: 基础配置字典
        preset_name: 预设名称
        
    Returns:
        Dict: 合并后的配置字典
    """
    preset = get_preset(preset_name)
    
    # 深度合并
    import copy
    merged_config = copy.deepcopy(base_config)
    
    if "split" in preset:
        if "split" not in merged_config:
            merged_config["split"] = {}
        merged_config["split"].update(preset["split"])
    
    return merged_config














































































