import asyncio
import sys
from pathlib import Path

# 添加 d:/anti 到 sys.path
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core/rekordbox-mcp")

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from pyrekordbox import Rekordbox6Database
    from sqlalchemy import text
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

async def diagnostic_search():
    db = RekordboxDatabase()
    try:
        await db.connect()
        rb_db = Rekordbox6Database()
        
        print(f"--- [Rekordbox Diagnostic Search] ---")
        
        # 1. 尝试全量计数
        tracks = list(rb_db.get_content())
        print(f"Total tracks in get_content(): {len(tracks)}")
        
        target_titles = ["hype boy", "ditto", "attention", "omg", "eta", "super shy", "cookie", "hurt", "bubble gum", "how sweet"]
        matches = []
        for t in tracks:
            title_lower = str(t.Title).lower()
            if any(target in title_lower for target in target_titles):
                matches.append(t)
        
        if matches:
            print(f"\nFound {len(matches)} matches by title. IDs:")
            for t in matches:
                print(f"ID:{t.ID}")
        else:
            print("No tracks matching common NewJeans titles found.")

        await db.disconnect()
    except Exception as e:
        print(f"Error during diagnostic: {e}")

if __name__ == "__main__":
    asyncio.run(diagnostic_search())
