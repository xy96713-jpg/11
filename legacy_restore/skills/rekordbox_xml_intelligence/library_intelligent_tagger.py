#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library Intelligent Tagger (V4.0) - [曲库多维智能打标引擎]
=========================================================
功能：
1. 继承 Rekordbox 播放列表大类。
2. 识别女团代际 (1st-5th Gen)。
3. 识别 Remix / Original 版本。
4. 标注 Happy / Electronic 等情绪极性。
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set

# 设置路径以引用现有模块
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

try:
    from pyrekordbox import Rekordbox6Database
except ImportError:
    print("Error: pyrekordbox not found.")
    sys.exit(1)

# Import atomicity manager
try:
    from core.cache_manager import save_cache_atomic
except ImportError:
    sys.path.append(str(BASE_DIR))
    from core.cache_manager import save_cache_atomic

# --- 配置：代际映射表 (扩充版) ---
KPOP_GENS = {
    "1st Gen": ["S.E.S", "Fin.K.L", "H.O.T", "Shinhwa", "g.o.d", "Baby V.O.X", "Turbo", "Sechs Kies"],
    "2nd Gen": ["Girls' Generation", "Girls Generation", "SNSD", "少女时代", "Kara", "Wonder Girls", "2NE1", "T-ara", "BigBang", "Super Junior", "SHINee", "f(x)", "After School", "Infinite", "Miss A", "Sistar", "Brown Eyed Girls"],
    "3rd Gen": ["Twice", "Blackpink", "Red Velvet", "BTS", "EXO", "GFriend", "Mamamoo", "Seventeen", "Got7", "I.O.I", "Wanna One", "AOA", "Apink", "Winner", "IKON"],
    "4th Gen": ["IVE", "NewJeans", "aespa", "LE SSERAFIM", "LESSERAFIM", "ITZY", "(G)I-DLE", "G-IDLE", "GIDLE", "STAYC", "NMIXX", "Kep1er", "Tomorrow X Together", "TXT", "Stray Kids", "Enhypen", "NCT", "Treasure"],
    "5th Gen": ["BabyMonster", "Babymon", "ILLIT", "Kiss of Life", "Kiof", "ZEROBASEONE", "ZB1", "RIIZE", "TWS", "BoyNextDoor"]
}

class LibraryTagger:
    def __init__(self, cache_path: str = "song_analysis_cache.json"):
        self.cache_path = Path(cache_path)
        self.db = Rekordbox6Database()
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if self.cache_path.exists():
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        save_cache_atomic(self.cache, str(self.cache_path))

    def run(self):
        print("--- [Library-IQ] 启动多维智能打标系统 ---")
        
        # 1. 建立播放列表映射
        pl_map = self._build_playlist_map()
        print(f"已映射 {len(pl_map)} 个播放列表关联")

        # 2. 获取所有音轨
        content = list(self.db.get_content())
        total_db = len(content)
        print(f"检测到 RB 数据库音轨数: {total_db}")
        
        # 路径到缓存键的预映射（提升性能）
        path_to_key = {}
        for key, entry in self.cache.items():
            p = entry.get('file_path', '').replace('\\', '/').lower()
            path_to_key[p] = key

        count = 0
        missing_count = 0
        for item in content:
            # 使用 FolderPath 替代 Location
            file_path = getattr(item, 'FolderPath', '')
            if not file_path: continue
            
            clean_db_path = file_path.replace('\\', '/').lower()
            if clean_db_path.startswith('file://localhost/'):
                clean_db_path = clean_db_path.replace('file://localhost/', '')
            if ':' in clean_db_path and clean_db_path.startswith('/'):
                clean_db_path = clean_db_path[1:]

            entry_key = path_to_key.get(clean_db_path)
            if not entry_key:
                if missing_count < 3:
                    print(f"[DEBUG] 匹配失败: DB({clean_db_path})")
                missing_count += 1
                continue

            cache_entry = self.cache[entry_key]
            # 初始化 tags
            if 'analysis' not in cache_entry: cache_entry['analysis'] = {}
            tags = set(cache_entry['analysis'].get('tags', []))

            # --- A. 播放列表继承 ---
            if item.ID in pl_map:
                for pl_name in pl_map[item.ID]:
                    tags.add(f"Playlist:{pl_name}")

            # --- B. 版本属性识别 ---
            title = (item.Title or "").lower()
            if any(k in title for k in ["remix", "edit", "bootleg", "rework", "flip", "vip"]):
                tags.add("Ver:Remix")
            else:
                tags.add("Ver:Original")

            # --- C. 女团/艺人代际识别 ---
            artist = (getattr(item, 'ArtistName', '') or "").lower()
            found_gen = False
            for gen, artists in KPOP_GENS.items():
                if any(a.lower() in artist for a in artists):
                    tags.add(f"Era:{gen}")
                    found_gen = True
                    break
            
            # 如果是 K-Pop 播放列表但没识别出代际，尝试根据路径或文件名兜底
            if not found_gen and any("k-pop" in t.lower() for t in tags):
                if any(x in title or x in artist for x in ["gen1", "gen2", "gen3", "gen4", "gen5"]):
                    # 简单匹配文字描述
                    pass 

            # --- D. 情绪与质感 (基于现有分析数据 - 对齐 SKILL.md 规范) ---
            analysis = cache_entry['analysis']
            valence = analysis.get('valence', 0.5)
            energy = analysis.get('energy', 50)
            
            # 清除旧标签（可选，为了保持纯净）
            tags.discard("Mood:Happy")
            tags.discard("Mood:Moody")
            tags.discard("Energy:Intense")
            tags.discard("Energy:Chill")

            # 严格对齐 SKILL.md 的 4 大核心极性
            if energy >= 60:
                if valence >= 0.5:
                    tags.add("Mood:Party/Excited")
                else:
                    tags.add("Mood:Dark/Intense")
            else: # energy < 60
                if valence >= 0.5:
                    tags.add("Mood:Chill/Dreamy")
                else:
                    tags.add("Mood:Melancholy/Deep")

            # 归并回缓存
            cache_entry['analysis']['tags'] = sorted(list(tags))
            count += 1

        self._save_cache()
        print(f"打标完成！已为 {count} 首歌曲补全多维标签。")

    def _build_playlist_map(self) -> Dict[int, List[str]]:
        """建立 ContentID -> [PlaylistNames] 的映射"""
        mapping = {}
        pls = list(self.db.get_playlist())
        for pl in pls:
            try:
                # 获取该播放列表下的所有歌曲
                songs = self.db.get_playlist_songs(PlaylistID=pl.ID)
                for s in songs:
                    if s.ContentID not in mapping:
                        mapping[s.ContentID] = []
                    mapping[s.ContentID].append(pl.Name)
            except:
                continue
        return mapping

if __name__ == "__main__":
    tagger = LibraryTagger()
    tagger.run()
