#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-Pop 3 Track Test V2 - 精简专业标点 (仅 A/B/C)
使用 Rekordbox 真实拍点数组进行精准对齐
"""

import os
import shutil
import json
from pathlib import Path
from pyrekordbox.rbxml import RekordboxXml
import sys

sys.path.insert(0, str(Path("D:/anti")))
try:
    from skills.cueing_intelligence.scripts.pro import professional_quantize, analyze_track_grid_anchor
except ImportError:
    # Fallback for older skill import if the new one isn't available
    from skills.skill_pro_cueing_v2 import generate_pro_cues_v2

def test_kpop_3_v2():
    print("=== Testing 3 K-Pop Tracks with V2 Pro Cueing (A/B/C Only) ===")
    
    # 加载缓存
    cache_path = Path("D:/anti/song_analysis_cache.json")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    path_map = {}
    for key, val in cache.items():
        if isinstance(val, dict) and val.get('_type') == 'path_index':
            clean_path = key.replace('path::', '').replace('\\', '/').lower()
            if clean_path.startswith('d:/'): clean_path = clean_path[3:]
            path_map[clean_path] = val.get('ref')

    # 测试歌曲
    source_tracks = [
        {"title": "MAMAMOO - HIP", "path": "D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3", "db_id": "119209545"},
        {"title": "SOOJIN - TyTy", "path": "D:/song/SOOJIN - TyTy (ayuwooh Remix).mp3", "db_id": "173507071"},
        {"title": "LIKEY Remix", "path": "D:/song/kpop house/LIKEY Remix.mp3", "db_id": "248424027"}
    ]
    
    output_dir = Path("D:/生成的set/kpop_v2_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_xml = "D:/生成的set/AI_KPOP_3_V2.xml"
    
    xml = RekordboxXml(name="rekordbox", version="6.0.0", company="Pioneer DJ")
    test_tracks = []
    
    for i, src in enumerate(source_tracks):
        src_path = src['path']
        if not os.path.exists(src_path):
            print(f"Skipping {src_path} (not found)")
            continue
            
        # 复制文件
        new_filename = f"V2_KPOP_{i+1}.mp3"
        new_path = (output_dir / new_filename).as_posix()
        shutil.copy2(src_path, new_path)
        
        # 查找分析缓存
        ref = None
        fname = os.path.basename(src_path).lower()
        for p, r in path_map.items():
            if fname in p:
                ref = r; break
        
        if ref and ref in cache:
            data = cache[ref]
            analysis = data.get('analysis', {})
            duration = analysis.get('duration', 180)
            
            print(f"\nProcessing V2: {src['title']}")
            
            # 提取人声数据，解决“各自为战”问题
            analysis = data.get('analysis', {})
            vocal_regions = analysis.get('vocal_regions', [])
            duration = analysis.get('duration', 180)
            
            print(f"\nProcessing V2: {src['title']}")
            
            # 使用 V2 生成器 - 现在整合了 PSSI 段落、PQTZ 网格和 Vocals 人声
            pro_result = generate_pro_cues_v2(
                content_id=src['db_id'],
                duration=duration,
                vocal_regions=vocal_regions
            )
            
            bpm = pro_result['bpm']
            anchor = pro_result['anchor']
            
            print(f"  Grid: Anchor={anchor:.3f}s, BPM={bpm}, Phrases={len(pro_result.get('memory_cues', []))}")
            
            # 创建 Track
            track = xml.add_track(new_path)
            track.set("Name", f"!! V2 {src['title']} !!")
            track.set("Artist", "AI Pro V2")
            track.set("AverageBpm", f"{bpm:.6f}")
            track.set("TotalTime", int(duration))
            track.set("Tonality", analysis.get('key', '1A'))
            
            # TEMPO 使用真实 anchor
            track.add_tempo(Inizio=f"{anchor:.6f}", Bpm=f"{bpm:.6f}", Metro="4/4", Battito=1)
            
            # 仅添加 A/B/C 三点，提高精度
            for char, cue in pro_result['cues'].items():
                print(f"  {char}: {cue['Name']} @ {cue['Start']:.6f}s")
                track.add_mark(Name=cue['Name'], Type="cue", Start=f"{cue['Start']:.6f}", Num=cue['Num'])
            
            # Memory Cues (段落提示)
            for mc in pro_result['memory_cues']:
                track.add_mark(Name=mc['Name'], Type="cue", Start=f"{mc['Start']:.6f}", Num=-1)
            
            test_tracks.append(track)
        else:
            print(f"No cache for: {src['title']}")

    if test_tracks:
        pl = xml.add_playlist("!!! AI_V2_KPOP_TEST !!!")
        for t in test_tracks:
            pl.add_track(t.TrackID)
        
        xml.save(out_xml)
        print(f"\n[SUCCESS] V2 Pro Cueing XML: {out_xml}")
    else:
        print("Error: No tracks processed.")

if __name__ == "__main__":
    test_kpop_3_v2()
