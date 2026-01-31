#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Loader Module
负责加载 config/dj_rules.yaml 用户配置，提供统一的规则访问接口。
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# 尝试导入 PyYAML，如果不存在则使用简易解析
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

class ConfigLoader:
    _instance = None
    _rules = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_rules()
        return cls._instance
    
    def _load_rules(self):
        """加载 dj_rules.yaml"""
        # 默认规则
        defaults = {
            'phrase_bars': 16,
            'phrase_dist_beats_threshold': 1.2,
            'phrase_penalty_cap': 0.55,
            'min_mix_window_len_sec': 12.0,
            'min_window_margin_sec': 4.0,
            'min_overlap_capacity_sec': 6.0,
            'key_compat_threshold': 70.0,
            'key_penalty_cap': 0.8,
            'genre_incompat_penalty': 0.6,
            'energy_jump_threshold': 10.0,
            'energy_jump_scale': 20.0,
            'energy_jump_penalty_cap': 0.8,
            'vocal_overlap_weight': 20.0,
            'chorus_overlap_penalty': 15.0,
            'enable_vocal_timeline_check': True,
            'enable_chorus_overlap_check': True,
            'vocal_clash_penalty_cap': 0.9,
            'rekordbox_metadata_priority': True,
            'bpm_range_min': 65.0,
            'bpm_range_max': 195.0
        }
        
        self._rules = defaults.copy()
        
        # 定位配置文件
        # 假设当前文件在 D:/anti/core/config_loader.py
        # config 在 D:/anti/config/dj_rules.yaml
        base_dir = Path(__file__).parent.parent
        config_path = base_dir / "config" / "dj_rules.yaml"
        
        if not config_path.exists():
            print(f"[WARN] Config file not found at {config_path}, using defaults.")
            return

        try:
            if HAS_YAML:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config and isinstance(user_config, dict):
                        self._rules.update(user_config)
                        print(f"[INFO] Loaded DJ rules from {config_path} (PyYAML)")
            else:
                self._parse_yaml_manually(config_path)
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}, using defaults.")

    def _parse_yaml_manually(self, path: Path):
        """简易 YAML 解析器 (当 PyYAML 不可用时)"""
        print(f"[INFO] PyYAML not found. Using manual parser for {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        key, val_str = line.split(':', 1)
                        key = key.strip()
                        val_str = val_str.split('#')[0].strip() # 去除行内注释
                        
                        # 类型转换
                        val = val_str
                        if val_str.lower() == 'true': val = True
                        elif val_str.lower() == 'false': val = False
                        else:
                            try:
                                if '.' in val_str: val = float(val_str)
                                else: val = int(val_str)
                            except:
                                pass # keep as string
                        
                        self._rules[key] = val
        except Exception as e:
            print(f"[WARN] Manual parsing error: {e}")

    @property
    def rules(self) -> Dict[str, Any]:
        return self._rules

# 便捷访问函数
def load_dj_rules() -> Dict[str, Any]:
    return ConfigLoader().rules
