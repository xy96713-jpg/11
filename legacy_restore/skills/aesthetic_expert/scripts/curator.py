#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aesthetic Curator Skill (V4.0) - [最强大脑审美引擎]
===================================================
通过分析曲风（Genre）、情感（Mood）和节奏纹理，提供超越物理参数的“审美匹配”逻辑。
"""

from typing import Dict, List, Tuple, Optional
import math

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
        """从能量和人声比例等推断情感标签"""
        energy = track.get('energy', 50)
        vocal_ratio = track.get('vocal_ratio', 0.5)
        genre = (track.get('genre') or '').lower()
        
        if energy > 75:
            if "techno" in genre or "dark" in genre: return "Dark"
            return "Uplifting"
        elif energy < 40:
            if vocal_ratio < 0.3: return "Chill"
            return "Deep"
        return "Neutral"

    def calculate_aesthetic_match(self, t1: Dict, t2: Dict) -> Tuple[float, Dict]:
        """
        计算两首歌之间的“美学和谐度” (0-100)
        """
        # 兼容性处理：如果输入是原始对象，尝试提取 analysis 块
        t1 = t1.get('analysis', t1)
        t2 = t2.get('analysis', t2)

        score = 70.0 # 基础分
        details = {}

        g1 = (t1.get('genre') or '').lower()
        g2 = (t2.get('genre') or '').lower()
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

        # --- E. [NEW V7.5] V35 Molecular Vibe Matching ---
        vibe_sum1 = t1.get('vibe_summary', '')
        vibe_sum2 = t2.get('vibe_summary', '')
        
        if vibe_sum1 and vibe_sum2:
            def parse_vibe(v_sum):
                parts = v_sum.split(" | ")
                d = {}
                for p in parts:
                    if ":" in p:
                        k, v = p.split(": ", 1)
                        d[k.lower()] = v.lower()
                return d
            
            dna1 = parse_vibe(vibe_sum1)
            dna2 = parse_vibe(vibe_sum2)
            
            dna_bonus = 0
            # 1. 时代质感一致性 (Texture Eras)
            # 拒绝：Lo-fi Texture x Ultra-Digital/Silk
            tex1, tex2 = dna1.get('texture', ''), dna2.get('texture', '')
            if tex1 and tex2:
                if (tex1 == 'lo-fi' and tex2 in ['silk', 'clean', 'ultra-digital']) or \
                   (tex2 == 'lo-fi' and tex1 in ['silk', 'clean', 'ultra-digital']):
                    dna_bonus -= 12
                    details['v35_texture_clash'] = "⚠️ Era Texture Clash (Lo-fi vs Hi-fi) -12"
                elif tex1 == tex2:
                    dna_bonus += 8
                    details['v35_texture_match'] = f"V35 Texture Match ({tex1.capitalize()}) +8"

            # 2. 空间听感对齐 (Spatial Field)
            s1_field, s2_field = dna1.get('space', ''), dna2.get('space', '')
            if s1_field and s2_field:
                if s1_field == s2_field:
                    dna_bonus += 5
                    details['v35_space_match'] = f"Spatial Harmony ({s1_field.capitalize()}) +5"
                elif (s1_field == 'ethereal' and s2_field == 'deep') or (s1_field == 'deep' and s2_field == 'ethereal'):
                    dna_bonus += 10
                    details['v35_space_synergy'] = "Cinematic Spatial Synergy +10"

            score += dna_bonus

        return max(0.0, min(100.0, score)), details

    def get_mix_bible_advice(self, t1: Dict, t2: Dict) -> Dict:
        """根据流派返回最强混音建议"""
        g2 = (t2.get('genre') or '').lower()
        
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
