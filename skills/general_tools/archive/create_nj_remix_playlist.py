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

async def create_nj_playlist():
    db = RekordboxDatabase()
    try:
        await db.connect()
        rb_db = Rekordbox6Database()
        
        print("--- [Creating NewJeans Remix Playlist] ---")
        
        # 1. 查找歌曲
        tracks = list(rb_db.get_content())
        target_titles = ["hype boy", "ditto", "attention", "omg", "eta", "super shy", "cookie", "hurt", "bubble gum", "how sweet"]
        
        matches = []
        for t in tracks:
            # 搜索逻辑：标题包含关键词 OR 路径包含 newjeans
            title_lower = str(t.Title).lower()
            location = getattr(t, 'Location', '') or ""
            
            title_match = any(target in title_lower for target in target_titles)
            path_match = "newjeans" in location.lower() or "뉴진스" in location.lower()
            
            if title_match or path_match:
                matches.append(t)
        
        print(f"Found {len(matches)} NewJeans related tracks in DB.")
        
        if not matches:
            print("No tracks found to add to playlist.")
            return

        # 2. 创建播放列表
        playlist_name = "NJ_V5_Session"
        print(f"Creating/Locating playlist: '{playlist_name}'...")
        
        # 检查是否已存在
        existing_playlists = list(rb_db.get_playlist())
        target_playlist = None
        for p in existing_playlists:
            if p.Name == playlist_name:
                target_playlist = p
                break
        
        if target_playlist:
            print(f"Playlist already exists (ID: {target_playlist.ID}). Clearing content...")
            # 注意：pyrekordbox 暂时不支持直接清空，我们只能尝试往里加
            playlist_id = target_playlist.ID
        else:
            print("Creating new playlist...")
            # 使用 MCP 的 create_playlist 功能
            new_pl = rb_db.create_playlist(playlist_name)
            # 必须 commit 才能获取 ID
            rb_db.commit()
            
            # 重新获取以拿到 ID (create_playlist 返回的对象可能没有 ID 更新)
            existing_playlists = list(rb_db.get_playlist())
            for p in existing_playlists:
                if p.Name == playlist_name:
                    target_playlist = p
                    break
            
            if target_playlist:
                playlist_id = target_playlist.ID
                print(f"Playlist created successfully (ID: {playlist_id})")
            else:
                print("Failed to verify created playlist.")
                return

        # 3. 添加歌曲
        print(f"Adding {len(matches)} tracks to playlist {playlist_id}...")
        
        added_count = 0
        current_songs = list(rb_db.get_playlist_songs(PlaylistID=playlist_id))
        existing_content_ids = [s.ContentID for s in current_songs]
        
        for t in matches:
            # 强制转换为 int
            try:
                tid = int(t.ID)
                pid = int(playlist_id)
                
                if tid not in existing_content_ids:
                    rb_db.add_to_playlist(pid, tid)
                    added_count += 1
            except Exception as e:
                print(f"Failed to add track {t.ID}: {e}")
        
        rb_db.commit()
        print(f"✅ Successfully added {added_count} new tracks to '{playlist_name}'.")
        
        # 4. 立即验证
        print("Verifying playlist content...")
        final_songs = list(rb_db.get_playlist_songs(PlaylistID=int(playlist_id)))
        print(f"Playlist now contains {len(final_songs)} tracks.")
        
        if len(final_songs) > 0:
            print("Tracks verified in DB.")
        else:
            print("WARNING: Playlist is still empty!")

        await db.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_nj_playlist())
