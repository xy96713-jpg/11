import asyncio
import sys
from pathlib import Path

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase

async def main():
    db = RekordboxDatabase()
    await db.connect()
    pls = await db.get_playlists()
    print("Available Playlists:")
    for p in pls:
        if not p.is_folder:
            print(f"- {p.name} (Tracks: {p.track_count})")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
