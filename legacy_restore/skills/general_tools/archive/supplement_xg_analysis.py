import asyncio
import sys
import json
from pathlib import Path

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase
from core.cache_manager import load_cache, save_cache_atomic

async def audit_xg_dance_energy():
    db = RekordboxDatabase()
    await db.connect()
    
    cache = load_cache()
    
    # 获取曲库所有曲目，不再使用 Small Limit
    all_ts = await db.get_most_played_tracks(limit=10000)
    print(f"Total potential tracks in DB: {len(all_ts)}")
    
    core_tracks = []
    for t in all_ts:
        # 极度宽泛的原始匹配：包含 XG 或者是新专辑
        search_blob = f"{t.title} {t.artist} {t.album} {t.file_path}".upper()
        if "XG" in search_blob or "CORE" in search_blob:
            core_tracks.append(t)
            
    print(f"Found {len(core_tracks)} tracks matching XG/CORE keywords.")

    updated_cache = False
    for t in core_tracks:
        path = t.file_path.replace('\\', '/')
        if path not in cache:
            cache[path] = {
                'file_path': t.file_path,
                'track_info': {'title': t.title, 'artist': t.artist},
                'analysis': {'bpm': t.bpm, 'key': t.key, 'energy': 50, 'tags': []}
            }
            
        analysis = cache[path].get('analysis', {})
        
        # --- 精确审计 XG 'THE CORE' 能量图谱 ---
        
        # 1. 慢歌 (Slow / Chill)
        if any(x in t.title.upper() for x in ["4 SEASONS", "PS118"]):
            analysis['energy'] = 25
            analysis['genre'] = 'R&B / Slow Jam'
            analysis['vocal_ratio'] = 0.8 # 人声为主
            analysis['tags'] = list(set(analysis.get('tags', []) + ['Slow', 'Vibe']))
            print(f"Supplemented SLOW: {t.title}")
            updated_cache = True

        # 2. 巅峰舞曲 (High Energy / Peak)
        elif any(x in t.title.upper() for x in ["ROCK THE BOAT", "GALA", "HYPNOTIZE"]):
            analysis['energy'] = 90
            analysis['genre'] = 'Hard Club / House'
            analysis['vocal_ratio'] = 0.4 # 律动为主
            analysis['tags'] = list(set(analysis.get('tags', []) + ['Dance', 'Peak']))
            print(f"Supplemented PEAK: {t.title}")
            updated_cache = True

        # 3. 标准舞曲 (Mid-High Energy)
        elif any(x in t.title.upper() for x in ["SOMETHING", "IYKYK", "TAKE MY BREATH", "NO GOOD"]):
            analysis['energy'] = 75
            analysis['genre'] = 'Electro Pop'
            analysis['tags'] = list(set(analysis.get('tags', []) + ['Dance']))
            print(f"Supplemented DANCE: {t.title}")
            updated_cache = True
            
    if updated_cache:
        save_cache_atomic(cache)
        print("Analysis cache successfully atomic-saved with XG 'THE CORE' profiles.")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(audit_xg_dance_energy())
