import asyncio
import sys
from pathlib import Path

# 添加 d:/anti 到 sys.path 以挂载 core 模块
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core/rekordbox-mcp")

try:
    from rekordbox_mcp.database import RekordboxDatabase
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

async def list_playlists():
    db = RekordboxDatabase()
    try:
        await db.connect()
        playlists = await db.get_playlists()
        print(f"{'ID':<10} | {'Name':<40} | {'Tracks':<10}")
        print("-" * 65)
        for p in playlists:
            if not p.is_folder:
                name = p.name if p.name else "Unnamed"
                if "newjeans" in name.lower():
                    print(f"{p.id:<10} | {name:<40} | {p.track_count:<10}")
        await db.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_playlists())
