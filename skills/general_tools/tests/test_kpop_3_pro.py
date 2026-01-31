#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-Pop 3 Track Test - Using Pro Cueing Logic
使用专业的结构感知标点逻辑
"""

from pyrekordbox.rbxml import RekordboxXml
import os
import shutil
import json
import sys
from pathlib import Path

# 添加项目路径以导入专业模块
sys.path.insert(0, str(Path("D:/anti")))
from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format

def test_kpop_3_tracks_pro():
    print("=== Testing 3 K-Pop Tracks with Pro Cueing Logic ===")
    
    # 1. 加载缓存
    cache_path = Path("D:/anti/song_analysis_cache.json")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    path_map = {}
    for key, val in cache.items():
        if isinstance(val, dict) and val.get('_type') == 'path_index':
            clean_path = key.replace('path::', '').replace('\\', '/').lower()
            if clean_path.startswith('d:/'): clean_path = clean_path[3:]
            path_map[clean_path] = val.get('ref')

    # 2. 选择 kpop house 里的 3 首歌
    source_tracks = [
        {"title": "MAMAMOO - HIP Test", "path": "D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3"},
        {"title": "SOOJIN - TyTy Test", "path": "D:/song/SOOJIN - TyTy (ayuwooh Remix).mp3"},
        {"title": "LIKEY Remix Test", "path": "D:/song/kpop house/LIKEY Remix.mp3"}
    ]
    
    output_dir = "D:/生成的set/kpop_pro_test"
    os.makedirs(output_dir, exist_ok=True)
    out_xml = "D:/生成的set/AI_KPOP_3_PRO.xml"
    
    xml = RekordboxXml(name="rekordbox", version="6.0.0", company="Pioneer DJ")
    test_tracks = []
    
    for i, src in enumerate(source_tracks):
        src_path = src['path']
        if not os.path.exists(src_path):
            print(f"Skipping {src_path} (not found)")
            continue
            
        # 复制为新文件，彻底绕过 Rekordbox 缓存
        new_filename = f"AI_KPOP_PRO_{i+1}.mp3"
        new_path = os.path.join(output_dir, new_filename).replace('\\', '/')
        shutil.copy2(src_path, new_path)
        
        # 查找分析缓存
        ref = None
        fname = os.path.basename(src_path).lower()
        for p, r in path_map.items():
            if fname in p:
                ref = r
                break
        
        if ref and ref in cache:
            data = cache[ref]
            analysis = data.get('analysis', {})
            bpm = analysis.get('bpm', 120)
            duration = analysis.get('duration', 180)
            
            print(f"Processing with Pro Cueing: {src['title']}")
            print(f"  - BPM: {bpm}, Duration: {duration}s")
            print(f"  - Structure: {data.get('structure', 'N/A')}")
            
            # 【关键】使用专业的 generate_hotcues 函数
            raw_cues = generate_hotcues(
                new_path,
                bpm=bpm,
                duration=duration,
                structure=data  # 传入完整的结构数据
            )
            
            # 转换为 Rekordbox 格式
            rb_cues = hotcues_to_rekordbox_format(raw_cues)
            
            # 添加到 XML
            track = xml.add_track(new_path)
            track.set("Name", f"!! {src['title']} (Pro) !!")
            track.set("Artist", "AI Pro Cueing")
            track.set("AverageBpm", bpm)
            track.set("TotalTime", int(duration))
            track.set("Tonality", analysis.get('key', '1A'))
            
            # 注入网格 (使用 anchor)
            anchor = raw_cues.get('anchor', 0.0)
            track.add_tempo(Inizio=anchor, Bpm=bpm, Metro="4/4", Battito=1)
            
            # 注入专业标点
            for char, cue in rb_cues.items():
                if cue['Num'] == -1:  # Memory Cue
                    track.add_mark(Name=cue['Name'], Type="cue", Start=cue['Start'], Num=-1)
                else:  # HotCue A-H
                    track.add_mark(Name=cue['Name'], Type="cue", Start=cue['Start'], Num=cue['Num'])
                print(f"  - {char}: {cue['Name']} @ {cue['Start']}s")
            
            test_tracks.append(track)
        else:
            print(f"No cache for: {src['title']}")

    # 加入播放列表
    if test_tracks:
        pl = xml.add_playlist("!!! AI_KPOP_3_PRO !!!")
        for t in test_tracks:
            pl.add_track(t.TrackID)
        
        xml.save(out_xml)
        print(f"\n[SUCCESS] K-Pop 3 Track Pro Test XML: {out_xml}")
    else:
        print("Error: No tracks processed.")

if __name__ == "__main__":
    test_kpop_3_tracks_pro()
