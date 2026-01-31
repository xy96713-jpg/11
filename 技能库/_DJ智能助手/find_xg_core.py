import asyncio
import sys
from pathlib import Path

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase
from core.cache_manager import load_cache

async def get_xg_tracks():
    db = RekordboxDatabase()
    await db.connect()
    
    # 获取全部曲目
    all_tracks = await db.get_most_played_tracks(limit=5000)
    
    print("--- Searching for ANY matching XG/Core tracks ---")
    for t in all_tracks:
        search_str = f"{t.title} {t.artist} {t.album} {t.file_path}".lower()
        if "xg" in search_str or "core" in search_str:
             print(f"{t.title} | {t.bpm} | {t.key} | {t.album} | {t.file_path}")
            
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(get_xg_tracks())
