#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narrative Set Planner (V5.0) - [叙事规划与构思引擎]
===================================================
本模块基于 IntelligenceResearcher 提供的知识图谱，实现“故事驱动”的排序规划。
它可以理解复杂的文化主题，并据此调整 Sorter 的评分权重。
"""

from typing import Dict, List, Tuple, Optional
try:
    from skill_intelligence_researcher import IntelligenceResearcher
except ImportError:
    from skills.skill_intelligence_researcher import IntelligenceResearcher

class NarrativePlanner:
    def __init__(self, researcher: Optional[IntelligenceResearcher] = None):
        self.researcher = researcher or IntelligenceResearcher()
        self.active_theme: Optional[str] = None
        self.theme_keywords: List[str] = []

    def set_theme(self, theme_query: str):
        """
        解析并设置当前 Set 的主轴
        例如: "从 Y2K 怀旧到未来主义的跨代演变"
        """
        self.active_theme = theme_query
        # 简易分词/关键词提取逻辑（未来可集成 LLM 解析）
        self.theme_keywords = [
            kw for kw in [
                "y2k", "nostalgia", "futurism", "girls", "power", "retro", "tech",
                "jersey", "club", "kpop", "idol", "dance", "electronic", "vibe"
            ]
            if kw in theme_query.lower()
        ]
        print(f"[Narrative] 已激活主题: {theme_query} (检测到关键词: {self.theme_keywords})")

    def calculate_narrative_score(self, t1: Dict, t2: Dict) -> Tuple[float, Dict]:
        """
        计算在该主题背景下，从 t1 过渡到 t2 的“叙事一致性”分数 (0-100)
        """
        base_score, logic = self.researcher.calculate_narrative_link(t1, t2)
        
        # 主题强化分数 (Contextual Boost)
        theme_bonus = 0
        details = {"base_knowledge": logic}

        if self.active_theme:
            # 检查 track 2 是否符合当前主题大方向
            info2 = self.researcher.get_entity_info(t2.get('artist', ''))
            if info2:
                # 检查描述或故事标签是否命中了主题关键词
                matched_kws = [kw for kw in self.theme_keywords if kw in str(info2).lower()]
                if matched_kws:
                    theme_bonus = 15 * len(matched_kws)
                    details['theme_boost'] = f"叙事命中主题 [{', '.join(matched_kws)}] +{theme_bonus}"
        
        final_score = base_score + theme_bonus
        return min(100.0, final_score), details

    def get_narrative_advice(self, t1: Dict, t2: Dict) -> str:
        """为混音报告生成一段‘有深度的’音乐学说明"""
        # 【V6.0】增加女团/K-Pop 联动描述 (前置作为强力 fallback)
        def normalize_artist(a):
            if not a: return ""
            return a.split(" [")[0].split(" (")[0].strip()

        a1_norm = normalize_artist(t1.get('artist'))
        a2_norm = normalize_artist(t2.get('artist'))
        
        girl_groups = ["NewJeans", "XG", "aespa", "LE SSERAFIM", "IVE", "BLACKPINK", "ITZY", "NMIXX"]
        if any(gg.lower() in a1_norm.lower() for gg in girl_groups) and \
           any(gg.lower() in a2_norm.lower() for gg in girl_groups):
            g1 = [gg for gg in girl_groups if gg.lower() in a1_norm.lower()][0]
            g2 = [gg for gg in girl_groups if gg.lower() in a2_norm.lower()][0]
            return f"作为当代女子群像的代表，{g1} 与 {g2} 的无缝衔接，勾勒出新世代流行乐的韧性与活力。"

        info1 = self.researcher.get_entity_info(t1.get('artist', ''))
        info2 = self.researcher.get_entity_info(t2.get('artist', ''))
        
        if info1 and info2 and info1.get("era") and info2.get("era") and info1.get("era") != info2.get("era"):
            return f"这是一次从 {info1.get('era')} 到 {info2.get('era')} 的跨时空对话，展示了审美逻辑的连续转型。"
            
        # Fallback: 基于物理量的描述，避免"文化叙事"废话
        bpm1 = t1.get('bpm', 0)
        bpm2 = t2.get('bpm', 0)
        key1 = t1.get('key', '')
        key2 = t2.get('key', '')
        
        narrative = []
        if abs(bpm1 - bpm2) > 5:
            narrative.append("明显的律动能量变化")
        if key1 != key2:
            narrative.append("调性色彩的转换")
            
        if narrative:
            return f"本段过渡聚焦于{'与'.join(narrative)}，构建动态的听感层次。"
            
        return "" # 实在没话说就闭嘴，保持专业高冷

if __name__ == "__main__":
    # 单元测试
    planner = NarrativePlanner()
    planner.set_theme("探索 Y2K 怀旧背景下的女团力量")
    
    t1 = {"artist": "NewJeans", "title": "Attention"}
    t2 = {"artist": "aespa", "title": "Supernova"}
    
    score, d = planner.calculate_narrative_score(t1, t2)
    print(f"叙事评分: {score}")
    print(f"详情: {d}")
    print(f"专家建议: {planner.get_narrative_advice(t1, t2)}")
