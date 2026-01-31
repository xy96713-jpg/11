#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Script: Music Cognition (V5.0)
=========================================
验证 Narrative Planner 是否能正确识别文化连接，并演示 dynamic research 潜力。
"""

import sys
from pathlib import Path

# 设置路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))

from narrative_set_planner import NarrativePlanner
from skills.skill_intelligence_researcher import IntelligenceResearcher

def test_v5_cognition():
    print("=== [V5.0 Music Cognition Test] ===")
    
    researcher = IntelligenceResearcher()
    planner = NarrativePlanner(researcher=researcher)
    
    # 案例 1: 已知关系 (NewJeans -> PinkPantheress)
    # 逻辑：两者都受到 UK Garage 的影响 (Common Influence)
    t1 = {"artist": "NewJeans", "title": "OMG"}
    t2 = {"artist": "PinkPantheress", "title": "Boy's a liar"}
    
    print(f"\n[Test 1] 跨界审美连接: {t1['artist']} -> {t2['artist']}")
    score, d = planner.calculate_narrative_score(t1, t2)
    advice = planner.get_narrative_advice(t1, t2)
    
    print(f"叙事评分: {score}")
    print(f"AI 理由: {d.get('base_knowledge', 'N/A')}")
    print(f"专家建议: {advice}")
    
    # 案例 2: 设置叙事主题 (Y2K Futurism)
    print("\n[Test 2] 设置主题蓝图: 'Y2K 怀旧背景下的女团力量'")
    planner.set_theme("探索 Y2K 怀旧背景下的女团力量")
    
    # 检查 aespa 是否命中主题（具有 Metallic Texture, AI 等标签）
    t3 = {"artist": "aespa", "title": "Supernova"}
    score_v2, d_v2 = planner.calculate_narrative_score(t1, t3)
    
    print(f"主题强化评分: {score_v2} (含主题奖分)")
    if 'theme_boost' in d_v2:
        print(f"主题命中: {d_v2['theme_boost']}")

    # 案例 3: 未知艺人 (演示如何触发扩展研究)
    print("\n[Test 3] 发现未知艺人: 'XG'")
    info = researcher.get_entity_info("XG")
    if not info:
        print("状态: 知识库未命中。建议启动 [Dynamic Web Research] 流程。")
        # 此处在生产环境中会触发 agent.search_web 并调用 researcher.inject_web_knowledge

if __name__ == "__main__":
    test_v5_cognition()
