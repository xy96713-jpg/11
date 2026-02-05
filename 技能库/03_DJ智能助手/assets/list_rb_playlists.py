import asyncio
import sys
from pathlib import Path

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
        for p in playlists:
            if not p.is_folder:
                print(f"{p.id} | {p.name}")
        await db.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_playlists())
