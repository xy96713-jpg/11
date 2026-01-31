import asyncio
import sys
from pathlib import Path

# 添加 d:/anti 到 sys.path
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core/rekordbox-mcp")

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from pyrekordbox import Rekordbox6Database
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

async def search_by_path():
    db = RekordboxDatabase()
    try:
        await db.connect()
        rb_db = Rekordbox6Database()
        
        print(f"--- [Rekordbox Path Search] ---")
        
        # 获取所有内容
        tracks = list(rb_db.get_content())
        print(f"Total tracks scanned: {len(tracks)}")
        
        targets = ["newjeans", "new jeans", "뉴진스"]
        matches = []
        
        for t in tracks:
            # 检查文件路径
            location = getattr(t, 'Location', '') or ""
            if any(target in location.lower() for target in targets):
                matches.append(t)
        
        if matches:
            print(f"\nFound {len(matches)} matches by file path:")
            print(f"{'Artist':<20} | {'Title':<40} | {'Path':<10}")
            print("-" * 100)
            for t in matches[:20]: # 展示前20个
                artist = getattr(t, 'ArtistName', '') or ""
                if not artist and hasattr(t, 'Artist'):
                    artist = getattr(t.Artist, 'Name', '') or ""
                
                location = getattr(t, 'Location', '') or ""
                # 简化路径显示
                filename = Path(location).name
                
                print(f"{str(artist)[:20]:<20} | {str(t.Title)[:40]:<40} | ...{filename}")
                
            # 统计一下 Artist 名字的分别
            artists = {}
            for t in matches:
                a = getattr(t, 'ArtistName', '') or ""
                if not a and hasattr(t, 'Artist'):
                    a = getattr(t.Artist, 'Name', '') or ""
                artists[str(a)] = artists.get(str(a), 0) + 1
            
            print("\nArtist Name Distribution found in these files:")
            for a, count in artists.items():
                print(f"  - '{a}': {count} tracks")
                
        else:
            print("No tracks found with 'NewJeans' in file path.")

        await db.disconnect()
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_by_path())
