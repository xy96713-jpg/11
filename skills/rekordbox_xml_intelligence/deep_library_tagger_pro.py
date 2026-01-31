#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Library Tagger Pro (V5.1) - [全量深度打标专家]
=================================================
1. 遍历 RB 数据库中 100% 的曲目。
2. 应用 7 大维度打标算法。
3. 注入 Intelligence Researcher 文化深度标签。
4. 全量持久化至 song_analysis_cache.json。
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

# 尝试导入依赖
try:
    from pyrekordbox import Rekordbox6Database
    from skills.skill_intelligence_researcher import IntelligenceResearcher
except ImportError:
    print("Error: Missing pyrekordbox or local skills. Please ensure environment is ready.")
    sys.exit(1)

# --- 配置：代际与版本字典 (集大成版) ---
KPOP_GENS = {
    "1st Gen": ["S.E.S", "Fin.K.L", "H.O.T", "Shinhwa", "g.o.d", "Baby V.O.X", "Turbo", "Sechs Kies"],
    "2nd Gen": ["Girls' Generation", "Girls Generation", "SNSD", "少女时代", "Kara", "Wonder Girls", "2NE1", "T-ara", "BigBang", "Super Junior", "SHINee", "f(x)", "After School", "Infinite", "Miss A", "Sistar", "Brown Eyed Girls", "T-ARA"],
    "3rd Gen": ["Twice", "Blackpink", "Red Velvet", "BTS", "EXO", "GFriend", "Mamamoo", "Seventeen", "Got7", "I.O.I", "Wanna One", "AOA", "Apink", "Winner", "IKON", "Day6", "Monsta X"],
    "4th Gen": ["IVE", "NewJeans", "aespa", "LE SSERAFIM", "LESSERAFIM", "ITZY", "(G)I-DLE", "G-IDLE", "GIDLE", "STAYC", "NMIXX", "Kep1er", "Tomorrow X Together", "TXT", "Stray Kids", "Enhypen", "NCT", "Treasure", "Xdinary Heroes", "Billlie"],
    "5th Gen": ["BabyMonster", "Babymon", "ILLIT", "Kiss of Life", "Kiof", "ZEROBASEONE", "ZB1", "RIIZE", "TWS", "BoyNextDoor", "UNIS", "MEOVV"]
}

VERSION_KEYWORDS = {
    "Remix": ["remix", "bootleg", "flip", "rework", "mashup"],
    "Edit": ["edit", "vip", "cut", "short"],
    "Instrumental": ["instrumental", "backing", "karaoke"],
    "Acapella": ["acapella", "vocal only"],
    "Extended": ["extended", "intro edit", "club mix", "original mix"],
    "Live": ["live", "concert", "performance"]
}

MOOD_THRESHOLDS = {
    "Euphoric": {"valence": 0.8, "energy": 0.8},
    "Happy": {"valence": 0.65, "energy": 0.5},
    "Moody": {"valence": 0.35, "energy": 0.4},
    "Intense": {"energy": 0.85},
    "Chill": {"energy": 0.35},
    "Dark": {"valence": 0.2, "energy": 0.6},
    "Electronic": {"tags": ["electronic", "techno", "house", "bass"]} # 补遗性质
}

class DeepLibraryTaggerPro:
    def __init__(self, cache_path: str = "song_analysis_cache.json"):
        self.cache_path = Path(cache_path)
        self.db = Rekordbox6Database()
        self.researcher = IntelligenceResearcher()
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if self.cache_path.exists():
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _build_playlist_map(self) -> Dict[str, List[str]]:
        pl_map = {}
        print("[DEBUG] 正在扫描播放列表层级...")
        for pl in self.db.get_playlist():
            pl_name = pl.Name or "Unnamed"
            if any(x in pl_name.lower() for x in ["histories", "all tracks", "itunes", "采样"]):
                continue
            
            try:
                # DjmdPlaylist -> Songs (DjmdSongPlaylist) -> ContentID
                count = 0
                for song_link in pl.Songs:
                    cid = getattr(song_link, 'ContentID', None)
                    if cid:
                        if cid not in pl_map: pl_map[cid] = []
                        if pl_name not in pl_map[cid]:
                            pl_map[cid].append(pl_name)
                            count += 1
                if count > 0:
                    print(f"  - 映射播放列表: {pl_name} ({count} 首)")
            except Exception as e:
                # print(f"  - 跳过播放列表 {pl_name}: {e}")
                pass
        return pl_map

    def run(self):
        print("--- [Deep-Tag-Pro] 开启全库深度分析 ---")
        pl_map = self._build_playlist_map()
        print(f"统计: 已建立 {len(pl_map)} 首音轨的分类归属关系。")

        content = list(self.db.get_content())
        total = len(content)
        print(f"准备分析 {total} 首音轨...")

        # 路径预匹配映射，提高效率
        path_to_key = {}
        for key, entry in self.cache.items():
            p = entry.get('file_path', '').replace('\\', '/').lower()
            path_to_key[p] = key

        stats = {"tagged": 0, "new": 0, "updates": 0, "dims": {}}
        
        for item in content:
            file_path = getattr(item, 'FolderPath', '')
            if not file_path: continue
            
            clean_path = file_path.replace('\\', '/').lower()
            if clean_path.startswith('file://localhost/'):
                clean_path = clean_path.replace('file://localhost/', '')
            if ':' in clean_path and clean_path.startswith('/'):
                clean_path = clean_path[1:]

            entry_key = path_to_key.get(clean_path)
            
            # 使用大写的 ID
            cid = getattr(item, 'ID', None)
            if not cid: continue

            # 如果缓存中没有，创建一个空条目
            if not entry_key:
                entry_key = f"auto_{cid}"
                self.cache[entry_key] = {
                    "file_path": file_path,
                    "title": getattr(item, 'Title', 'Unknown'),
                    "artist": getattr(item, 'ArtistName', 'Unknown'),
                    "analysis": {"tags": []},
                    "source": "db_auto_discovery"
                }
                stats["new"] += 1
            
            entry = self.cache[entry_key]
            # 【V5.1 固化】确保 top-level 基础元数据完整
            entry['artist'] = getattr(item, 'ArtistName', 'Unknown')
            entry['title'] = getattr(item, 'Title', 'Unknown')
            entry['bpm'] = getattr(item, 'BPM', 0) / 100.0
            
            if 'analysis' not in entry: entry['analysis'] = {}
            current_tags = set(entry['analysis'].get('tags', []))
            
            # --- 维度 1: 播放列表大类 (Ancestor) ---
            if cid in pl_map:
                for pl in pl_map[cid]:
                    current_tags.add(f"Playlist:{pl}")

            # --- 维度 2: 文化代际 (Era) ---
            artist = (item.ArtistName or "").lower()
            title = (item.Title or "").lower()
            target_text = f"{artist} {title}"
            
            for gen, artists in KPOP_GENS.items():
                if any(a.lower() in target_text for a in artists):
                    current_tags.add(f"Era:{gen}")
            
            # 补丁：从缓存年份打标
            year = getattr(item, 'ReleaseYear', 0)
            if year:
                if 1980 <= year < 1990: current_tags.add("Era:80s")
                elif 1990 <= year < 2000: current_tags.add("Era:90s")
                elif 2000 <= year < 2010: current_tags.add("Era:2000s")
                elif 2010 <= year < 2020: current_tags.add("Era:2010s")

            # --- 维度 3: 版本属性 (Version) ---
            for ver, kws in VERSION_KEYWORDS.items():
                if any(kw in target_text for kw in kws):
                    current_tags.add(f"Ver:{ver}")

            # --- 维度 4: 情绪极性 (Aura/Mood) ---
            valence = entry.get('valence') or entry.get('analysis', {}).get('valence')
            energy = entry.get('energy') or entry.get('analysis', {}).get('energy', 50)
            
            if valence is not None:
                if valence >= 0.7: current_tags.add("Mood:Happy")
                elif valence <= 0.3: current_tags.add("Mood:Blue")
                else: current_tags.add("Mood:Neutral")
            
            # --- 维度 4.5: 能量梯度 (Energy Tier) ---
            if energy >= 85: current_tags.add("Energy:Tier5-Peak")
            elif energy >= 70: current_tags.add("Energy:Tier4-Intense")
            elif energy >= 50: current_tags.add("Energy:Tier3-Steady")
            elif energy >= 30: current_tags.add("Energy:Tier2-Build")
            else: current_tags.add("Energy:Tier1-Chill")

            # --- 维度 5: 核心流派 (Refined Genre) ---
            db_genre = (getattr(item, 'GenreName', '') or "").lower()
            if db_genre:
                current_tags.add(f"Genre:{db_genre.capitalize()}")

            # --- 维度 6: 全球知识图谱注入 (Intelligence) ---
            knowledge = self.researcher.get_entity_info(item.ArtistName or "")
            if knowledge:
                for theme in knowledge.get("themes", []):
                    current_tags.add(f"Theme:{theme}")
                for st in knowledge.get("story_tags", []):
                    current_tags.add(f"Story:{st}")

            # --- 维度 7: BPM 区分 (Functional) ---
            bpm_raw = getattr(item, 'BPM', 0)
            if bpm_raw:
                bpm = bpm_raw / 100.0 # 修正 Rekordbox DB 单位
                range_start = (int(bpm) // 5) * 5
                current_tags.add(f"BPM:{range_start}-{range_start+5}")

            # 更新缓存
            entry['analysis']['tags'] = sorted(list(current_tags))
            stats["tagged"] += 1
            
            if stats["tagged"] % 100 == 0:
                print(f"进度: {stats['tagged']}/{total}...")

        self._save_cache()
        print(f"\n✅ 打标完成！")
        print(f"   总分析数: {stats['tagged']}")
        print(f"   新增探测: {stats['new']}")
        print(f"   全库覆盖率: {(stats['tagged']/total)*100:.1f}%")
        print(f"   平均每首标签数: {sum(len(v['analysis'].get('tags', [])) for v in self.cache.values()) / len(self.cache):.1f}")

if __name__ == "__main__":
    tagger = DeepLibraryTaggerPro()
    tagger.run()
