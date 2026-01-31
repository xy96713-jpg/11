import os
import shutil
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
        tid = 9900000 + i
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
        
        # 注入 Tempo (BeatGrid)，Rekordbox 有时需要这个来对齐标点
        ET.SubElement(entry, "TEMPO", 
                     Inizio="0.0", 
                     Bpm=str(track.get('bpm', 120)), 
                     Metro="4/4", 
                     Battito="1")
        
        # 注入 HotCues (A-E) 和 Memory Cues
        for hc in track.get('cues', []):
            num = str(hc['kind'] - 1) if hc['kind'] > 0 else "-1"
            # 关键修复：使用 POSITION_MARK 而不是 POSITION
            # 关键修复：使用 Start 而不是 Time
            # 关键修复：添加 Type="0" (cue)
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

def generate_absolute_proof():
    print("=== AI Cue Final Proof Generator ===")
    
    # 1. 加载缓存
    cache_path = Path("D:/anti/song_analysis_cache.json")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    # 建立路径映射
    path_map = {}
    for key, val in cache.items():
        if isinstance(val, dict) and val.get('_type') == 'path_index':
            clean_path = key.replace('path::', '').replace('\\', '/').lower()
            if clean_path.startswith('d:/'): clean_path = clean_path[3:]
            path_map[clean_path] = val.get('ref')

    # 2. 定位 3 个确认存在的源文件 (从之前的 check_d_song.py 结果挑选)
    source_tracks = [
        {"title": "LE SSERAFIM - Proof Test", "path": "D:/song/kpop/LE SSERAFIM - Eve, Psyche & The Bluebeard’s wife (BRLLNT Edit) [1597547181].mp3"},
        {"title": "NewJeans - Proof Test", "path": "D:/song/kpop/NewJeans - OMG (BRLLNT Remix) [1416029752].mp3"},
        {"title": "House Mix - Proof Test", "path": "D:/song/house 摇摆/I Like It (MFM Edit) [1550571445].mp3"}
    ]
    
    test_tracks = []
    output_dir = "D:/生成的set/proof_files"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Selecting {len(source_tracks)} tracks for absolute proof...")
    
    for i, src in enumerate(source_tracks):
        src_path = src['path']
        if not os.path.exists(src_path):
            print(f"Warning: Source not found {src_path}, skipping.")
            continue
            
        # 复制文件到一个新位置，确保 Rekordbox 把它当成新歌
        new_filename = f"AI_PROOF_SONG_{i+1}.mp3"
        new_path = os.path.join(output_dir, new_filename).replace('\\', '/')
        shutil.copy2(src_path, new_path)
        print(f"  Copied to: {new_path}")
        
        # 查找分析数据
        ref = None
        # 查找逻辑
        fname = os.path.basename(src_path).lower()
        for p, r in path_map.items():
            if fname in p:
                ref = r
                break
        
        if ref and ref in cache:
            found_analysis = cache[ref]['analysis']
            bpm = found_analysis['bpm']
            duration = found_analysis.get('duration', 180)
            bar_sec = (60.0 / bpm) * 4.0
            
            a_in = found_analysis.get('mix_in_point', 1.0)
            c_out = found_analysis.get('mix_out_point', duration - 10)
            
            track_data = {
                'title': src['title'],
                'artist': "!! ANTIGRAVITY AI !!",
                'file_path': new_path,
                'bpm': bpm,
                'key': found_analysis.get('key', ''),
                'cues': [
                    {'kind': 1, 'time': round(a_in, 3), 'name': '!! AI_IN_A !!'},
                    {'kind': 2, 'time': round(a_in + (8 * bar_sec), 3), 'name': '!! AI_FULL_B !!'},
                    {'kind': 3, 'time': round(c_out - (8 * bar_sec), 3), 'name': '!! AI_OUT_C !!'},
                    {'kind': 4, 'time': round(c_out, 3), 'name': '!! AI_END_D !!'},
                    {'kind': 5, 'time': round(found_analysis.get('drop_point', 30), 3), 'name': '!! AI_DROP_E !!'}
                ]
            }
            test_tracks.append(track_data)
            
    if test_tracks:
        out_xml = "D:/生成的set/AI_ABSOLUTE_PROOF.xml"
        simple_xml_export(test_tracks, out_xml, "!!! AI_PROOF_PLAYLIST !!!")
        print(f"\n[SUCCESS] XML 导出成功: {out_xml}")
        print(f"已创建 {len(test_tracks)} 个不重名的测试文件在 {output_dir}")
        print("请在 Rekordbox 导入此 XML，并查看 !!! AI_PROOF_PLAYLIST !!!")
    else:
        print("Error: No tracks processed.")

if __name__ == "__main__":
    generate_absolute_proof()
