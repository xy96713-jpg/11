import asyncio
import sys
from pathlib import Path
import json

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase
from core.cache_manager import load_cache

async def main():
    db = RekordboxDatabase()
    await db.connect()
    
    found_tracks = await db.search_tracks_by_filename("忍者")
    if not found_tracks:
        all_tracks = await db.get_most_played_tracks(limit=1000)
        found_tracks = [t for t in all_tracks if "忍者" in t.title]
        
    if not found_tracks:
        print("❌ 找不到曲目：忍者")
        await db.disconnect()
        return

    target_track = found_tracks[0]
    target_path = target_track.file_path.replace('\\', '/')
    print(f"🎯 Target: {target_track.title} at {target_path}")

    cache = load_cache()
    # 路径映射
    path_map = {v.get('file_path', '').replace('\\', '/'): v for v in cache.values()}
    
    analysis = path_map.get(target_path)
    if not analysis:
        # 模糊匹配
        matches = [v for k, v in path_map.items() if "忍者" in k]
        if matches:
            print(f"Found fuzzy match: {matches[0].get('file_path')}")
            analysis = matches[0]
            
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
