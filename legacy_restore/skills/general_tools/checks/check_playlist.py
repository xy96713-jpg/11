import asyncio
import sys
from pathlib import Path

# 添加路径必须在 import 之前
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase

async def main():
    db = RekordboxDatabase()
    await db.connect()
    pls = await db.get_playlists()
    target = next((p for p in pls if '现代remix' in p.name), None)
    if target:
        print(f"TARGET_FOUND: {target.name}")
        print(f"ID: {target.id}")
        print(f"Tracks: {target.track_count}")
    else:
        print("TARGET_NOT_FOUND")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
