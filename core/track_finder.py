import os
import sys
import glob

# Try to import pyrekordbox for DB access
try:
    from pyrekordbox import Rekordbox6Database
    HAS_PYREKORDBOX = True
except ImportError:
    HAS_PYREKORDBOX = False

SEARCH_ROOTS = [r"d:\anti", r"d:\song", r"d:\song\kpop", r"C:\Users\Administrator\Downloads"]

def smart_find_track(keyword, use_db=True, fuzzy=True):
    """
    智能搜歌工具
    策略：
    1. Rekordbox 数据库查询 (最快，最准)
    2. 文件系统快速扫描 (fallback)
    """
    found_paths = []
    
    # Strategy 1: Rekordbox DB
    if use_db and HAS_PYREKORDBOX:
        try:
            # Silence irrelevant startup warnings
            import logging
            logging.getLogger('pyrekordbox').setLevel(logging.ERROR)
            
            db = Rekordbox6Database()
            all_songs = db.get_content()
            
            kw_min = keyword.lower()
            for song in all_songs:
                if not song.Title: continue
                
                match = False
                if fuzzy:
                    if kw_min in song.Title.lower():
                        match = True
                else:
                    if kw_min == song.Title.lower():
                        match = True
                        
                if match:
                    # 返回丰富数据：路径 + DB 元数据
                    # pyrekordbox DjmdContent 原始属性通常为 Uppercase
                    # BPM 在 DB 中是整数 (BPM * 100)
                    db_bpm = (song.BPM / 100.0) if hasattr(song, 'BPM') and song.BPM else None
                    db_key = song.KeyName if hasattr(song, 'KeyName') else None
                    
                    found_paths.append({
                        "path": song.FolderPath,
                        "db_bpm": db_bpm,
                        "db_key": db_key,
                        "source": "DB"
                    })
                    print(f"  [DB_HIT] Found in Rekordbox: {song.FolderPath} (BPM: {db_bpm}, Key: {db_key})")
                            
        except Exception as e:
            print(f"  [DB_WARN] Rekordbox lookup failed: {e}")
            
    if found_paths:
        return found_paths
        
    # Strategy 2: Filesystem
    print(f"  [FS_SEARCH] Searching filesystem (Fallback)...")
    for root_dir in SEARCH_ROOTS:
        if not os.path.exists(root_dir): continue
        
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if not file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                    continue
                
                if keyword.lower() in file.lower():
                    path = os.path.join(root, file)
                    found_paths.append({
                        "path": path,
                        "db_bpm": None,
                        "db_key": None,
                        "source": "FS"
                    })
                    print(f"  [FS_HIT] Found on Disk: {path}")
                        
    return found_paths

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Core Track Finder")
    parser.add_argument("keyword", help="Track title or keyword")
    args = parser.parse_args()
    
    results = smart_find_track(args.keyword)
    if not results:
        print("No tracks found.")
    else:
        print(f"Found {len(results)} matches.")
