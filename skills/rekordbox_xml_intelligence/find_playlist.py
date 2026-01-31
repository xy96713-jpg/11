import asyncio
from rekordbox_mcp.database import RekordboxDatabase

async def main():
    db = RekordboxDatabase()
    await db.connect()
    pls = await db.get_playlists()
    for p in pls:
        if not p.is_folder and p.track_count > 5:
            print(f"PLAYLIST_NAME: {p.name}")
            break
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
