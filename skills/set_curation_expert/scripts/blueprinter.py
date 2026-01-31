#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set Blueprinter (V5.0) - [叙事蓝图引擎]
====================================
负责管理和解释 DJ Set 的结构化蓝图（Chapter-based Blueprinting）。
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SetBlueprinter:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "d:/anti/config/dj_blueprints.yaml")
        self.blueprints = self._load_blueprints()
        self.active_blueprint = self.blueprints.get("club_standard", {})

    def _load_blueprints(self) -> Dict:
        merged_blueprints = {}
        
        # 1. 加载主配置文件
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and "blueprints" in data:
                        merged_blueprints.update(data["blueprints"])
            except Exception as e:
                print(f"[Blueprinter] 无法加载主蓝图配置: {e}")
        
        # 2. 扫描 blueprints 目录 (V6.0 新增)
        blueprints_dir = self.config_path.parent / "blueprints"
        if blueprints_dir.exists() and blueprints_dir.is_dir():
            for yaml_file in blueprints_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data and "name" in data:
                            # 使用文件名或内部 name 作为 key
                            key = yaml_file.stem
                            merged_blueprints[key] = data
                            print(f"[Blueprinter] 已加载扩展蓝图: {key}")
                except Exception as e:
                    print(f"[Blueprinter] 无法加载扩展蓝图 {yaml_file.name}: {e}")
                    
        return merged_blueprints

    def set_blueprint(self, blueprint_name: str):
        if blueprint_name in self.blueprints:
            self.active_blueprint = self.blueprints[blueprint_name]
            print(f"[Blueprinter] 已激活蓝图: {blueprint_name}")

    def get_phase_target(self, progress: float) -> Tuple[float, float, str, Dict]:
        """
        根据当前进度 (0.0 - 1.0) 返回对应的章节目标
        """
        chapters = self.active_blueprint.get("chapters", [])
        if not chapters:
            return (40.0, 70.0, "General", {})

        current_cumulative_percent = 0.0
        for chapter in sorted(chapters, key=lambda x: x.get('order', 0)):
            chapter_duration = chapter.get('duration_percent', 0) / 100.0
            current_cumulative_percent += chapter_duration
            
            if progress <= current_cumulative_percent or chapter == chapters[-1]:
                return (
                    chapter.get('energy_range', [40, 70])[0],
                    chapter.get('energy_range', [40, 70])[1],
                    chapter.get('name', 'Unknown'),
                    chapter
                )
        
        return (40.0, 70.0, "General", {})

if __name__ == "__main__":
    # 测试蓝图解析
    bp = SetBlueprinter()
    for p in [0.05, 0.25, 0.6, 0.95]:
        low, high, name, _ = bp.get_phase_target(p)
        print(f"进度 {p*100}% -> 章节: {name} (能量: {low}-{high})")
