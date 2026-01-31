import os
import json
import xml.etree.ElementTree as ET
from pyrekordbox import Rekordbox6Database
from pathlib import Path
from urllib.parse import quote

# 简化的 XML 导出逻辑 - 严格遵循 Rekordbox 6 Schema
def simple_xml_export(tracks, output_file, playlist_name):
    root = ET.Element("DJ_PLAYLISTS", version="1.0.0")
    product = ET.SubElement(root, "PRODUCT", Name="rekordbox", Version="6.0.0", Company="Pioneer DJ")
    collection = ET.SubElement(root, "COLLECTION", Entries=str(len(tracks)))
    
    track_ids = []
    for i, track in enumerate(tracks):
        tid = 9000000 + i
        track_ids.append(tid)
        
        file_path = track['file_path'].replace('\\', '/')
        if not file_path.startswith('/'): file_path = '/' + file_path
        location = f"file://localhost{quote(file_path)}"
        
        # 严格按照 PositionMark 要求的属性
        entry = ET.SubElement(collection, "TRACK", 
                             TrackID=str(tid),
                             Name=track.get('title', 'Unknown'),
                             Artist=track.get('artist', 'Unknown'),
                             Kind="Music File",
                             Tonality=track.get('key', ''),
                             AverageBpm=str(track.get('bpm', 0)),
                             TotalTime=str(int(track.get('duration', 180))),
                             Location=location)
        
        # 注入 Tempo (BeatGrid)
        ET.SubElement(entry, "TEMPO", 
                     Inizio="0.0", 
                     Bpm=str(track.get('bpm', 120)), 
                     Metro="4/4", 
                     Battito="1")
        
        # 注入 HotCues (A-E)
        for hc in track.get('cues', []):
            num = str(hc['kind'] - 1) if hc['kind'] > 0 else "-1"
            # 关键修复：使用 POSITION_MARK, Type="0", Start
            ET.SubElement(entry, "POSITION_MARK", 
                         Name=hc['name'], 
                         Type="0", 
                         Start=str(hc['time']), 
                         Num=num)
                             
    playlists = ET.SubElement(root, "PLAYLISTS")
    node = ET.SubElement(playlists, "NODE", Type="0", Name="ROOT", Count="1")
    pl_node = ET.SubElement(node, "NODE", Name=playlist_name, Type="1", KeyType="0", Entries=str(len(tracks)))
    for tid in track_ids:
        ET.SubElement(pl_node, "TRACK", Key=str(tid))
        
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

def generate_ai_standard_test():
    print("=== AI Professional Cue Standalone Generator ===")
    
    # 1. 加载缓存
    cache_path = Path("D:/anti/song_analysis_cache.json")
    if not cache_path.exists():
        print("Error: Cache not found.")
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    # 1b. 建立路径映射
    path_map = {} # path -> hash
    for key, val in cache.items():
        if isinstance(val, dict) and val.get('_type') == 'path_index':
            clean_path = key.replace('path::', '').replace('\\', '/').lower()
            if clean_path.startswith('d:/'): clean_path = clean_path[3:] # Match pyrekordbox style if needed
            path_map[clean_path] = val.get('ref')
    
    print(f"Path Map built with {len(path_map)} entries.")
    print("Sample Path Map keys:", list(path_map.keys())[:5])

    # 2. 连接数据库找没打点的歌
    from sqlalchemy import text
    db = Rekordbox6Database()
    # 优先选取 D:/song 目录下的歌，用户更熟悉 (比如 K-Pop 歌)
    all_content = db.session.execute(text("SELECT ID, Title, FileNameL, FolderPath, BPM, Length FROM djmdContent WHERE FolderPath LIKE 'D:/song/kpop%' OR Title LIKE '%NewJeans%' OR Title LIKE '%BLACKPINK%'")).fetchall()
    print(f"Database has {len(all_content)} candidate tracks.")
    
    test_tracks = []
    
    for i, row in enumerate(all_content):
        cid, title, fname, fpath, bpm_int, length = row
        artist = "AI Artist"
        
        # 查找缓存
        ref = None
        for p, r in path_map.items():
            if fname and fname.lower() in p:
                ref = r
                break
        
        if ref and ref in cache:
            data = cache[ref]
            if not isinstance(data, dict) or 'analysis' not in data:
                continue
            
            found_analysis = data['analysis']
            if 'bpm' not in found_analysis:
                continue
            
            # 【重要修复】检查是否已经有手动点位，如果有则跳过，我们只测 AI 补位
            cue_check = db.session.execute(text(f"SELECT ID FROM djmdCue WHERE ContentID = :cid AND Kind = 1 AND rb_local_deleted = 0"), {"cid": cid}).fetchone()
            if cue_check: continue

            print(f"Generating Professional Cues for: {title}")
            bpm = found_analysis['bpm']
            duration = found_analysis.get('duration', length if length else 180)
            bar_sec = (60.0 / bpm) * 4.0
            
            # AI 专家逻辑
            a_in = found_analysis.get('mix_in_point', 0.1)
            b_in = a_in + (8 * bar_sec) 
            d_out = found_analysis.get('mix_out_point', duration - 10)
            c_out = d_out - (8 * bar_sec)
            drop = found_analysis.get('drop_point') or (duration * 0.3)
            
            # 路径获取
            track_path = fpath.replace('\\', '/')
            if not os.path.exists(track_path):
                track_path = os.path.join(os.path.dirname(fpath), fname).replace('\\', '/')
            
            track_data = {
                'title': title,
                'artist': artist,
                'file_path': track_path, 
                'bpm': bpm,
                'key': found_analysis.get('key', ''),
                'cues': [
                    {'kind': 1, 'time': round(a_in, 3), 'name': 'AI Mix-In (A)'},
                    {'kind': 2, 'time': round(b_in, 3), 'name': 'AI Full (B)'},
                    {'kind': 3, 'time': round(c_out, 3), 'name': 'AI Mix-Out (C)'},
                    {'kind': 4, 'time': round(d_out, 3), 'name': 'AI End (D)'},
                    {'kind': 5, 'time': round(drop, 3), 'name': 'AI Drop (E)'},
                    {'kind': 0, 'time': round(a_in, 3), 'name': 'Start Marker'}, 
                    {'kind': 0, 'time': round(c_out, 3), 'name': 'Mix Ready'}
                ]
            }
            
            test_tracks.append(track_data)
            if len(test_tracks) >= 3: break

    if test_tracks:
        out_path = "D:/生成的set/AI_Professional_Cues.xml"
        simple_xml_export(test_tracks, out_path, "AI_Pro_Test_v2")
        print(f"\n[SUCCESS] XML 已导出: {out_path}")
        print("请注意：Time 字段现在已改为 SECONDS (如 14.28)，之前版本使用了毫秒导致不显示。")
    else:
        print("No suitable tracks found.")


if __name__ == "__main__":
    # 模拟 ET.text
    class TextMock:
        def __init__(self, s): self.s = s
        def __str__(self): return self.s
    ET.text = text if 'text' in globals() else lambda x: x # Use sqlalchemy text
    
    os.makedirs("D:/生成的set", exist_ok=True)
    generate_ai_standard_test()
