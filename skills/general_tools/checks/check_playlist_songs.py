from pyrekordbox import Rekordbox6Database

def check_playlist(playlist_name):
    try:
        db = Rekordbox6Database()
        # 查找播放列表
        playlists = db.get_playlist().all()
        target_pl = None
        for pl in playlists:
            if pl.Name == playlist_name:
                target_pl = pl
                break
        
        if not target_pl:
            print(f"[ERROR] 找不到播放列表: {playlist_name}")
            return

        print(f"[FOUND] 播放列表: {target_pl.Name} (ID: {target_pl.ID})")
        
        # 提取歌曲
        songs = list(target_pl.Songs)
        print(f"[INFO] 关联条目数量: {len(songs)}")
        
        for i, song_pl in enumerate(songs):
            song = song_pl.Content
            if song:
                artist = getattr(song, 'ArtistName', 'Unknown')
                title = getattr(song, 'Title', 'Unknown')
                bpm = getattr(song, 'BPM', 0) / 100.0
                print(f"  {i+1}. {artist} - {title} [BPM: {bpm}]")
            else:
                print(f"  {i+1}. [MISSING CONTENT] ContentID: {getattr(song_pl, 'ContentID', 'N/A')}")

    except Exception as e:
        import traceback
        print(f"[FATAL] 检查失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    check_playlist("现代remix")
