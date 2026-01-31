#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligence Researcher Skill (V5.0) - [词典与叙事探测内核]
=========================================================
本模块负责管理 music_knowledge_base.json，并提供基于语义的音乐学知识查询。
它支撑了从“数据点匹配”到“故事线匹配”的审美跨越。
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

class IntelligenceResearcher:
    def __init__(self, kb_path: str = "music_knowledge_base.json"):
        self.kb_path = Path(kb_path)
        # 默认知识库模板（如果不存在则初始化）
        self.default_kb = {
            "entities": {},
            "genres": {},
            "themes": {}
        }
        self.kb = self._load_kb()

    def _load_kb(self) -> Dict:
        if self.kb_path.exists():
            try:
                with open(self.kb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[RE-ERROR] 加载知识库失败: {e}")
        return self.default_kb

    def save_kb(self):
        try:
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.kb, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RE-ERROR] 保存知识库失败: {e}")

    def get_entity_info(self, name: str) -> Optional[Dict]:
        """获取艺人或团体的深度背景"""
        name_lower = name.lower().strip()
        # 简单匹配逻辑，未来可升级为模糊匹配
        for key, info in self.kb.get("entities", {}).items():
            if name_lower in key.lower() or key.lower() in name_lower:
                return info
        return None

    def get_genre_context(self, genre: str) -> Optional[Dict]:
        """获取流派的历史与文化背景"""
        return self.kb.get("genres", {}).get(genre.lower())

    def update_entity(self, name: str, data: Dict):
        """更新实体知识"""
        if "entities" not in self.kb: self.kb["entities"] = {}
        self.kb["entities"][name] = data
        self.save_kb()

    def calculate_narrative_link(self, track1_meta: Dict, track2_meta: Dict) -> Tuple[float, str]:
        """
        核心算法：计算两首曲目在“叙事深度”上的关联性
        返回: (得分 0-100, 逻辑说明)
        """
        score = 0
        reasons = []

        # 1. 艺人系谱关联 (Artist Genealogy)
        # 例如：NewJeans 受 90s UK Garage 影响，如果下一首是纯正的 UKG，得分加成
        info1 = self.get_entity_info(track1_meta.get('artist', ''))
        info2 = self.get_entity_info(track2_meta.get('artist', ''))

        if info1 and info2:
            # 检查共同的影响力或流变关系
            inf1 = set(info1.get("influences", []))
            inf2 = set(info2.get("influences", []))
            common = inf1.intersection(inf2)
            if common:
                score += 30
                reasons.append(f"共享文化根源: {list(common)[0]}")
            
            # 检查是否有显式的代际传承
            if info1.get("era") == info2.get("era"):
                score += 10
                reasons.append(f"时代共振 ({info1.get('era')})")

        # 2. 叙事主题匹配 (Theme Matching)
        t1_themes = set(track1_meta.get('themes', []))
        t2_themes = set(track2_meta.get('themes', []))
        common_themes = t1_themes.intersection(t2_themes)
        if common_themes:
            score += 20 * len(common_themes)
            reasons.append(f"主题契合: {', '.join(common_themes)}")

        return min(100.0, score), " | ".join(reasons)

if __name__ == "__main__":
    # 单元测试与初始化
    researcher = IntelligenceResearcher()
    # 注入一些种子数据用于验证
    researcher.update_entity("NewJeans", {
        "era": "4th Gen K-Pop",
        "description": "Y2K Nostalgia, Jersey Club fusion",
        "influences": ["UK Garage", "Baltimore Club", "90s Pop"],
        "themes": ["Retro-Futurism", "Youth", "Nostalgia"]
    })
    researcher.update_entity("PinkPantheress", {
        "era": "2020s Viral",
        "description": "Short-form UKG, Alt-Pop",
        "influences": ["UK Garage", "Drum and Bass"],
        "themes": ["Lo-fi", "Self-aware", "Nostalgia"]
    })
    
    match_score, explanation = researcher.calculate_narrative_link(
        {"artist": "NewJeans", "themes": ["Nostalgia"]},
        {"artist": "PinkPantheress", "themes": ["Nostalgia"]}
    )
    print(f"叙事匹配测试: {match_score} - {explanation}")
