from pyrekordbox.anlz import AnlzFile
import os
from pathlib import Path

def debug_pssi(content_id="248424027"): # LIKEY Remix
    try:
        anlz_base = Path(os.environ.get('APPDATA', '')) / 'Pioneer/rekordbox/share'
        # 我们需要找到 LIKEY Remix 的精确 ANLZ 文件夹，或者直接遍历
        # 暂时手动查找特定路径（从 verify_playlist_automation.py 逻辑中推断）
        # 这里我先扫描一下可能的 EXT 文件
        rel_path = "/PIONEER/USBANLZ/b3b/989ea-6b22-4467-bc13-8ddc323ee824/ANLZ0000.EXT"
        anlz_path = anlz_base / rel_path.lstrip('/')
        
        if not anlz_path.exists():
            print(f"File not found: {anlz_path}")
            # 尝试通过搜索找到它
            return
            
        anlz = AnlzFile.parse_file(str(anlz_path))
        pssi = anlz.get('PSSI')
        if not pssi:
            print("No PSSI tag found in EXT file.")
            return
            
        print(f"PSSI Content for {content_id} (LIKEY Remix):")
        for entry in pssi.entries:
            # 这里的 beat 是从 1 开始的
            # kind: 1:Intro, 2:Verse, 3:Chorus, 4:Down, 5:Up...
            print(f"Beat: {entry.beat}, Kind: {entry.kind}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_pssi()
