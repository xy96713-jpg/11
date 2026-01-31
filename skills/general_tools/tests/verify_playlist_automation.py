import os
import json
import sys
import shutil
import time
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET
from pyrekordbox import Rekordbox6Database
from pyrekordbox.anlz import AnlzFile
from sqlalchemy import text

# 项目路径定义
PROJECT_ROOT = Path(r"D:\anti")
OUTPUT_DIR = Path(r"D:\生成的set")
sys.path.insert(0, str(PROJECT_ROOT))

# 导入核心逻辑
from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format

def get_rekordbox_grid(content_id: str) -> tuple:
    """获取同步网格"""
    try:
        db = Rekordbox6Database()
        q = text('SELECT BPM, AnalysisDataPath FROM djmdContent WHERE ID = :cid')
        row = db.session.execute(q, {"cid": content_id}).fetchone()
        if not row: return None, None
        bpm = row[0] / 100.0
        anlz_rel_path = row[1]
        anlz_base = Path(os.environ.get('APPDATA', '')) / 'Pioneer/rekordbox/share'
        anlz_path = anlz_base / anlz_rel_path.lstrip('/')
        if not anlz_path.exists(): return None, bpm
        anlz = AnlzFile.parse_file(str(anlz_path))
        qtz = anlz.get('PQTZ')
        if qtz and len(qtz) >= 3 and len(qtz[2]) > 0:
            return float(qtz[2][0]), bpm
        return None, bpm
    except:
        return None, None

def verify_playlist_automation(playlist_id="226494199", playlist_name="House"):
    print(f"=== Brain DJ GOLD Automation: {playlist_name} ===")
    
    # 局部实例化的动态物理隔离
    local_ts = int(time.time())
    iso_dir = OUTPUT_DIR / f"gold_fix_{local_ts}"
    iso_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 加载 AI 缓存
    cache_path = PROJECT_ROOT / "song_analysis_cache.json"
    if not cache_path.exists():
        print(f"Error: Cache not found at {cache_path}")
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    path_map = {key.replace('path::', '').replace('\\', '/').lower(): val.get('ref') 
                for key, val in cache.items() if isinstance(val, dict) and val.get('_type') == 'path_index'}
    
    # 2. 获取数据库列表
    db = Rekordbox6Database()
    query = text("""
        SELECT c.ID, c.Title, a.Name as Artist, c.FileNameL, c.FolderPath, c.BPM, c.Length
        FROM djmdContent c
        JOIN djmdSongPlaylist sp ON c.ID = sp.ContentID
        LEFT JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE sp.PlaylistID = :playlist_id
    """)
    tracks = db.session.execute(query, {"playlist_id": playlist_id}).fetchall()
    print(f"Found {len(tracks)} tracks. Executing gold isolation...")

    processed_tracks = []
    seen_ids = set()
    
    for row in tracks:
        cid, title, artist, fname, fpath, bpm_int, length = row
        if cid in seen_ids: continue
        seen_ids.add(cid)
        
        src_path = fpath.replace('\\', '/')
        if not os.path.exists(src_path): continue
            
        ref = path_map.get(src_path.lower())
        if not ref:
            fname_lower = fname.lower()
            for p, r in path_map.items():
                if fname_lower in p:
                    ref = r; break
        
        if ref and ref in cache:
            data = cache[ref]
            analysis = data.get('analysis', {})
            
            # 物理隔离 + 黄金改名（彻底解决没改动错觉）
            new_fname = f"[GOLD] {fname}"
            dest_path = (iso_dir / new_fname).as_posix()
            shutil.copy2(src_path, dest_path)
            
            anchor, rb_bpm = get_rekordbox_grid(cid)
            bpm = rb_bpm if rb_bpm else analysis.get('bpm', 120.0)
            data['id'] = cid
            
            # V2 引擎生成：人声避让、Phrase 绑定、网格对齐
            raw_cues = generate_hotcues(
                dest_path, 
                bpm=bpm, 
                duration=analysis.get('duration', length), 
                structure=data,
                anchor=anchor or 0.0
            )
            
            processed_tracks.append({
                'title': f"[GOLD] {title}",
                'artist': artist or "",
                'file_path': dest_path,
                'bpm': bpm,
                'anchor': anchor or 0.0,
                'key': analysis.get('key', '1A'),
                'duration': analysis.get('duration', length),
                'cues': hotcues_to_rekordbox_format(raw_cues)
            })

    if not processed_tracks:
        print("[ERROR] No tracks successfully processed.")
        return

    # 3. 构建规范 XML
    root = ET.Element("DJ_PLAYLISTS", Version="1.0.0")
    ET.SubElement(root, "PRODUCT", Name="rekordbox", Version="6.0.0", Company="Pioneer DJ")
    collection = ET.SubElement(root, "COLLECTION", Entries=str(len(processed_tracks)))
    
    # 使用时间戳生成起始 ID
    start_id = (local_ts % 10000000) + 10000000
    
    for i, t in enumerate(processed_tracks):
        tid = start_id + i
        loc = f"file://localhost/{quote(t['file_path'].lstrip('/'))}"
        
        entry = ET.SubElement(collection, "TRACK", 
                             TrackID=str(tid), Name=t['title'], Artist=t['artist'],
                             Kind="Music File", Tonality=t['key'], AverageBpm=f"{t['bpm']:.6f}",
                             TotalTime=str(int(t['duration'])), Location=loc)
        
        ET.SubElement(entry, "TEMPO", Inizio=f"{t['anchor']:.6f}", Bpm=f"{t['bpm']:.6f}", Metro="4/4", Battito="1")
        
        # 严格 A-B-C 三点打点
        sorted_cues = sorted(t['cues'].values(), key=lambda x: x['Num'])
        for cue in sorted_cues:
            ET.SubElement(entry, "POSITION_MARK", 
                         Name=cue['Name'], Type="0", 
                         Start=f"{cue['Start']:.6f}", 
                         Num=str(cue['Num']))
                                 
    playlists = ET.SubElement(root, "PLAYLISTS")
    root_node = ET.SubElement(playlists, "NODE", Type="0", Name="ROOT", Count="1")
    pl_node = ET.SubElement(root_node, "NODE", Name=f"!!! GOLD {playlist_name} FIX !!!", Type="1", KeyType="0", Entries=str(len(processed_tracks)))
    for i in range(len(processed_tracks)):
        ET.SubElement(pl_node, "TRACK", Key=str(start_id + i))
        
    output_xml = OUTPUT_DIR / f"AI_GOLD_FIX_{playlist_name.upper()}.xml"
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)
    
    print(f"\n[SUCCESS] AI GOLD XML: {output_xml}")
    print(f"Exported to unique folder: {iso_dir}")

if __name__ == "__main__":
    verify_playlist_automation()
