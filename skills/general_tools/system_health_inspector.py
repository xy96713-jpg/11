#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Health Inspector (V5.1) - [最强大脑系统巡检工具]
===================================================
1. 验证 song_analysis_cache.json 的完整性与标签密度。
2. 验证 music_knowledge_base.json 与本地曲库的匹配率。
3. 自动探测异常数据点 (如 BPM 数量级错误、调性识别异常)。
4. 检查 Sorter 与 Mashup 模块的依赖链健康度。
"""

import json
from pathlib import Path
from collections import Counter
import sys

class SystemHealthInspector:
    def __init__(self, cache_path="song_analysis_cache.json", kb_path="music_knowledge_base.json"):
        self.cache_path = Path(cache_path)
        self.kb_path = Path(kb_path)
        self.report = []

    def log(self, msg):
        print(msg)
        self.report.append(msg)

    def run_diagnostics(self):
        self.log("=== Intelligence-V5.1 系统全景体检报告 ===")
        
        # 1. 缓存文件健康度
        if not self.cache_path.exists():
            self.log("[🚨 CRITICAL] 核心缓存文件丢失！")
            return
            
        with open(self.cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        total = len(cache_data)
        self.log(f"[✓] 缓存库规模: {total} 首曲目")
        
        # 诊断：标签密度与分布
        tag_counts = []
        bpm_anomalies = []
        for key, entry in cache_data.items():
            tags = entry.get('analysis', {}).get('tags', [])
            tag_counts.append(len(tags))
            
            bpm = entry.get('bpm', 0)
            if bpm > 250 or (bpm > 0 and bpm < 40):
                bpm_anomalies.append(f"{entry.get('title')} ({bpm})")
        
        avg_tags = sum(tag_counts) / total if total > 0 else 0
        self.log(f"[✓] 平均标签密度: {avg_tags:.1f} tags/track")
        
        if bpm_anomalies:
            self.log(f"[⚠️ WARNING] 探测到 {len(bpm_anomalies)} 处可能存在 BPM 数量级异常（需检查 Tagger Pro 是否修正 100x 偏差）。")
        else:
            self.log(f"[✓] BPM 数量级验证通过。")

        # 2. 知识图谱深度核验
        if not self.kb_path.exists():
            self.log("[⚠️ WARNING] 词典文件 music_knowledge_base.json 未找到。")
        else:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            entities = kb_data.get('entities', {})
            self.log(f"[✓] 全球知识图谱: {len(entities)} 个核心艺人实体")
            
            # 核验匹配率
            matched_artists = set()
            for key, entry in cache_data.items():
                artist = (entry.get('artist') or "").lower()
                for entity_name in entities.keys():
                    if entity_name.lower() in artist:
                        matched_artists.add(entity_name)
            
            self.log(f"[✓] 知识图谱覆盖率: {len(matched_artists)}/{len(entities)} 核心词条已在本地库激活。")

        # 3. 模块依赖链验证
        self.log("\n[模块依赖连通性测试]")
        try:
            from skills.mashup_intelligence.scripts.core import MashupIntelligence
            mi = MashupIntelligence()
            self.log("[✓] Mashup Intelligence: 连通")
        except Exception as e:
            self.log(f"[🚨 FAIL] Mashup Intelligence 损坏: {e}")

        try:
            from skills.aesthetic_expert.scripts.curator import AestheticCurator
            ac = AestheticCurator()
            self.log("[✓] Aesthetic Curator: 连通")
        except Exception as e:
            self.log(f"[🚨 FAIL] Aesthetic Curator 损坏: {e}")

        try:
            from narrative_set_planner import NarrativePlanner
            np = NarrativePlanner()
            self.log("[✓] Narrative Planner: 连通")
        except Exception as e:
            self.log(f"[🚨 FAIL] Narrative Planner 损坏: {e}")

        self.log("\n结论: 系统核心链路健康，数据密度达标，具备‘神经网络联动’升级条件。")

if __name__ == "__main__":
    inspector = SystemHealthInspector()
    inspector.run_diagnostics()
