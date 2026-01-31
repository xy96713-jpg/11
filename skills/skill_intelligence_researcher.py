#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligence Researcher Skill (V5.0) - [最强大脑：动态音乐知识库]
===========================================================
负责维护本地音乐知识体系，并在遇到未知艺人时通过联网搜索进行动态补全。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class IntelligenceResearcher:
    def __init__(self, knowledge_path: Optional[str] = None):
        self.knowledge_path = Path(knowledge_path or "d:/anti/music_knowledge_base.json")
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> Dict:
        if not self.knowledge_path.exists():
            return {"entities": {}, "genres": {}, "themes": {}}
        try:
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Researcher] 无法加载知识库: {e}")
            return {"entities": {}, "genres": {}, "themes": {}}

    def _save_knowledge(self):
        try:
            with open(self.knowledge_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Researcher] 无法保存知识库: {e}")

    def get_entity_info(self, artist_name: str) -> Optional[Dict]:
        """获取艺人的文化基因信息"""
        if not artist_name or artist_name == "Unknown":
            return None
            
        # 1. 优先从本地查询
        entity = self.knowledge["entities"].get(artist_name)
        if entity:
            return entity
            
        # 2. 尝试模糊匹配（处理 Case）
        for name, info in self.knowledge["entities"].items():
            if name.lower() == artist_name.lower():
                return info
                
        # 3. 如果本地没有，且是在交互模式或允许联网，则进行动态研究
        # 注意：此处通过 agent 的能力触发联网搜索，脚本本身提供逻辑
        return None

    def calculate_narrative_link(self, t1: Dict, t2: Dict) -> Tuple[float, str]:
        """
        计算两首歌之间的“叙事逻辑”得分 (0-100)
        """
        a1 = t1.get('artist', 'Unknown')
        a2 = t2.get('artist', 'Unknown')
        
        info1 = self.get_entity_info(a1)
        info2 = self.get_entity_info(a2)
        
        if not info1 or not info2:
            return 60.0, "基础过渡（未知叙事背景）"
            
        score = 70.0
        reasons = []
        
        # A. 时代连续性 (Temporal Continuity)
        if info1.get("era") == info2.get("era"):
            score += 15
            reasons.append(f"同属于 {info1['era']} 时代")
        
        # B. 影响因子 (Influences / Heritage)
        inf1 = set(info1.get("influences", []))
        inf2 = set(info2.get("influences", []))
        common = inf1.intersection(inf2)
        if common:
            score += 20
            reasons.append(f"共同受到 {', '.join(list(common)[:2])} 的影响")
            
        # C. 艺人直接关联 (Direct Influence)
        if a1 in info2.get("influences", []) or a2 in info1.get("influences", []):
            score += 25
            reasons.append(f"艺人之间存在明确的致敬或血缘关系")
            
        # D. 标签契合 (Story Tags)
        tags1 = set(info1.get("story_tags", []))
        tags2 = set(info2.get("story_tags", []))
        common_tags = tags1.intersection(tags2)
        if common_tags:
            score += 10
            reasons.append(f"共享叙事标签: {', '.join(list(common_tags)[:2])}")

        return min(100.0, score), " | ".join(reasons) if reasons else "文化背景相关的平滑过渡"

    def inject_web_knowledge(self, artist_name: str, research_data: Dict):
        """将从网络研究获取的知识注入本地库"""
        if artist_name and research_data:
            self.knowledge["entities"][artist_name] = research_data
            self._save_knowledge()
            print(f"[Researcher] 已成功将 {artist_name} 的文化基因存入核心知识库")

if __name__ == "__main__":
    # 单元测试
    res = IntelligenceResearcher()
    test_t1 = {"artist": "NewJeans"}
    test_t2 = {"artist": "PinkPantheress"}
    score, reason = res.calculate_narrative_link(test_t1, test_t2)
    print(f"叙事得分: {score} | 原因: {reason}")
