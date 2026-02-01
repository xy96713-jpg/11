#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aesthetic Curator Skill (V4.0) - [最强大脑审美引擎]
===================================================
通过分析曲风（Genre）、情感（Mood）和节奏纹理，提供超越物理参数的“审美匹配”逻辑。
"""

from typing import Dict, List, Tuple, Optional
import math
import sys
from pathlib import Path

# 【V11.0 Global DNS Sync】
try:
    from audio_dna import map_dna_features, calculate_dna_affinity
    DNA_SYNC_ENABLED = True
except ImportError:
    DNA_SYNC_ENABLED = False
    def map_dna_features(a): return a
    def calculate_dna_affinity(d1, d2): return 0.0, []

class AestheticCurator:
    # 1. 流派美学矩阵 (Genre Aesthetic Matrix)
    # 定义不同流派的灵魂属性：(推荐混音时长(小节), 核心手法, 情感倾向)
    GENRE_BIBLE = {
        "techno": {"bars": 32, "style": "Linear Blend (Linear EQ)", "vibe": "Hypnotic/Drive"},
        "melodic techno": {"bars": 48, "style": "Epic Multi-Layer Layering", "vibe": "Ethereal/Emotional"},
        "house": {"bars": 16, "style": "Bass Swap (EQ Cut)", "vibe": "Groovy/Uplifting"},
        "deep house": {"bars": 24, "style": "Warm Smooth Fade", "vibe": "Sophisticated/Slow"},
        "tech house": {"bars": 16, "style": "Percussive Energy Match", "vibe": "Rhythmic/Clean"},
        "disco": {"bars": 8, "style": "Phrase Swap / Filter Cut", "vibe": "Funky/Organic"},
        "trance": {"bars": 32, "style": "Anthemic Progression", "vibe": "Euphoric/High"},
        "hip hop": {"bars": 4, "style": "Quick Cut / Echo Out", "vibe": "Urban/Swagger"},
        "ambient": {"bars": 64, "style": "Texture Immersion", "vibe": "Space/Calm"},
        "drum and bass": {"bars": 16, "style": "Double Drop / Switch", "vibe": "Adrenaline/Fast"}
    }

    # 2. 情感流动推荐 (Emotional Navigation)
    # 推荐的“安全”与“出彩”的情感跳跃（Valence/Energy 变化倾向）
    EMOTION_FLOW = {
        "Uplifting": ["Uplifting", "Excited", "Neutral"],
        "Deep": ["Deep", "Dark", "Melancholy"],
        "Dark": ["Intense", "Dark", "Aggressive"],
        "Chill": ["Chill", "Deep", "Neutral"],
        "Aggressive": ["Intense", "Aggressive", "Dark"]
    }

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def get_track_vibe(self, track: Dict) -> str:
        """从能量、音色和人声比例推断情感标签 (V11.0 DNA)"""
        dna = map_dna_features(track.get('analysis', track))
        energy = dna.get('energy', 50)
        vocal_ratio = dna.get('vocal_ratio', 0.5)
        valence = dna.get('valence', 0.5)
        
        if energy > 75:
            if valence > 0.6: return "Uplifting"
            return "Intense"
        elif energy < 40:
            if vocal_ratio < 0.3: return "Chill"
            return "Deep"
        return "Neutral"

    def calculate_aesthetic_match(self, t1: Dict, t2: Dict) -> Tuple[float, Dict]:
        """
        计算两首歌之间的“美学和谐度” (0-100)
        """
        score = 70.0 # 基础分
        details = {}

        g1 = t1.get('genre', '').lower()
        g2 = t2.get('genre', '').lower()
        v1 = self.get_track_vibe(t1)
        v2 = self.get_track_vibe(t2)

        # A. 流派血缘一致性 (Genre Coherence)
        genre_bonus = 0
        if g1 and g2:
            if g1 == g2:
                 genre_bonus = 15
                 details['genre'] = f"Same Genre ({g1}) +15"
            elif self._are_genres_compatible(g1, g2):
                 genre_bonus = 8
                 details['genre'] = f"Compatible Genres ({g1}->{g2}) +8"
            else:
                 genre_bonus = -10
                 details['genre'] = f"Genre Clash ({g1}->{g2}) -10"
        score += genre_bonus

        # B. 情感流动一致性 (Vibe Flow)
        vibe_score = 0
        if v1 in self.EMOTION_FLOW and v2 in self.EMOTION_FLOW[v1]:
            vibe_score = 10
            details['vibe'] = f"Natural Flow ({v1}->{v2}) +10"
        elif v1 != v2:
            vibe_score = -5
            details['vibe'] = f"Vibe Shift ({v1}->{v2}) -5"
        score += vibe_score

        # C. [V11.0] 音频 DNA 亲和力 (Timbre & Groove Sync)
        dna1 = map_dna_features(t1.get('analysis', t1))
        dna2 = map_dna_features(t2.get('analysis', t2))
        dna_score, dna_tags = calculate_dna_affinity(dna1, dna2)
        
        # 将 DNA 分数映射到审美矩阵 (权重 20%)
        dna_bonus = dna_score * 0.2
        score += dna_bonus
        if dna_tags:
            details['dna_sync'] = f"DNA Affinity ({', '.join(dna_tags)}) +{dna_bonus:.1f}"

        # D. 标签亲和力 (Tag Affinity) - [NEW V4.0]
        tags1 = t1.get('tags', [])
        tags2 = t2.get('tags', [])
        if tags1 and tags2:
            tag_match_score = 0
            
            # 提取维度标签的辅助函数
            def get_dim_tags(tags, prefix):
                return [t[len(prefix):] for t in tags if t.startswith(prefix)]
            
            era1, era2 = get_dim_tags(tags1, "Era:"), get_dim_tags(tags2, "Era:")
            ver1, ver2 = get_dim_tags(tags1, "Ver:"), get_dim_tags(tags2, "Ver:")
            mood1, mood2 = get_dim_tags(tags1, "Mood:"), get_dim_tags(tags2, "Mood:")
            pl1, pl2 = get_dim_tags(tags1, "Playlist:"), get_dim_tags(tags2, "Playlist:")

            # 1. 时代一致性（如：同为二代女团）
            if era1 and era2 and any(e in era2 for e in era1):
                tag_match_score += 15
                details['tags_era'] = f"Same Era/Gen ({era1[0]}) +15"
            
            # 2. 版本一致性（如：同为 Remix）
            if ver1 and ver2 and any(v in ver2 for v in ver1):
                tag_match_score += 10
                details['tags_ver'] = f"Same Edit Style ({ver1[0]}) +10"

            # 3. 情绪一致性（如：同为欢乐）
            if mood1 and mood2 and any(m in mood2 for m in mood1):
                tag_match_score += 8
                details['tags_mood'] = f"Consistent Emotion ({mood1[0]}) +8"
            
            # 4. 播放列表大类一致性
            if pl1 and pl2 and any(p in pl2 for p in pl1):
                tag_match_score += 5
                details['tags_playlist'] = "Same Source Category +5"

            score += tag_match_score

        return max(0.0, min(100.0, score)), details

    def get_mix_bible_advice(self, t1: Dict, t2: Dict) -> Dict:
        """根据流派返回最强混音建议"""
        g2 = t2.get('genre', '').lower()
        
        # 匹配最接近的流派规则
        rule = self.GENRE_BIBLE.get("house") # 默认
        for key in self.GENRE_BIBLE:
            if key in g2:
                rule = self.GENRE_BIBLE[key]
                break
        
        return {
            "technique": rule["style"],
            "suggested_duration": f"{rule['bars']} bars",
            "vibe_target": rule["vibe"]
        }

    def _are_genres_compatible(self, g1: str, g2: str) -> bool:
        """扩展的流派美学兼容性矩阵"""
        compatibility_map = {
            "house": ["tech house", "deep house", "disco", "nu-disco", "melodic techno", "progressive house"],
            "techno": ["tech house", "minimal", "industrial", "dark techno", "ebm"],
            "melodic techno": ["progressive house", "deep house", "organic house", "trance", "melodic house"],
            "deep house": ["organic house", "melodic techno", "nu-disco", "chillout"],
            "hip hop": ["r&b", "funk", "soul", "lofi", "trap"],
            "ambient": ["chillout", "meditation", "deep house"]
        }
        
        # 双向检查逻辑：只要一方在另一方的邻居列表中即可
        for root, neighbors in compatibility_map.items():
            if root in g1:
                if any(n in g2 for n in neighbors): return True
            if root in g2:
                if any(n in g1 for n in neighbors): return True
        return False
