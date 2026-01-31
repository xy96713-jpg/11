#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-Pop 3 Track Test - Using Rekordbox Beat Grid Data
使用 Rekordbox 的网格数据进行精准标点
"""

from pyrekordbox.rbxml import RekordboxXml
from pyrekordbox.anlz import AnlzFile
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text
import os
import shutil
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path("D:/anti")))
from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format
from skills.skill_pro_cueing import professional_quantize, get_pro_label, identify_mix_type, generate_emergency_loop

def get_rekordbox_anchor(content_id: str) -> tuple:
    """
    从 Rekordbox 数据库和 ANLZ 文件获取网格信息
    Returns: (anchor_time, bpm) or (None, None) if not found
    """
    try:
        db = Rekordbox6Database()
        q = text('SELECT BPM, AnalysisDataPath FROM djmdContent WHERE ID = :cid')
        row = db.session.execute(q, {"cid": content_id}).fetchone()
        
        if not row:
            return None, None
            
        bpm_int, anlz_rel_path = row
        bpm = bpm_int / 100.0  # Rekordbox 存储为 14000 = 140.00 BPM
        
        # 构建 ANLZ 文件完整路径
        anlz_base = Path(os.environ.get('APPDATA', '')) / 'Pioneer/rekordbox/share'
        anlz_path = anlz_base / anlz_rel_path.lstrip('/')
        
        if not anlz_path.exists():
            print(f"  [WARN] ANLZ file not found: {anlz_path}")
            return None, bpm
            
        # 解析 ANLZ 文件
        anlz = AnlzFile.parse_file(str(anlz_path))
        qtz = anlz.get('PQTZ')
        
        if qtz and len(qtz) >= 3 and len(qtz[2]) > 0:
            anchor = float(qtz[2][0])  # 第一个拍子的时间
            print(f"  [GRID] Rekordbox Anchor: {anchor:.3f}s, BPM: {bpm}")
            return anchor, bpm
        
        return None, bpm
    except Exception as e:
        print(f"  [ERROR] Failed to get Rekordbox grid: {e}")
        return None, None

def test_kpop_3_tracks_rb_grid():
    print("=== Testing 3 K-Pop Tracks with Rekordbox Beat Grid ===")
    
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

    # 2. 选择 kpop house 里的 3 首歌 (带数据库 ID)
    source_tracks = [
        {"title": "MAMAMOO - HIP", "path": "D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3", "db_id": "119209545"},
        {"title": "SOOJIN - TyTy", "path": "D:/song/SOOJIN - TyTy (ayuwooh Remix).mp3", "db_id": "173507071"},
        {"title": "LIKEY Remix", "path": "D:/song/kpop house/LIKEY Remix.mp3", "db_id": "248424027"}
    ]
    
    output_dir = "D:/生成的set/kpop_rb_grid_test"
    os.makedirs(output_dir, exist_ok=True)
    out_xml = "D:/生成的set/AI_KPOP_3_RB_GRID.xml"
    
    xml = RekordboxXml(name="rekordbox", version="6.0.0", company="Pioneer DJ")
    test_tracks = []
    
    for i, src in enumerate(source_tracks):
        src_path = src['path']
        if not os.path.exists(src_path):
            print(f"Skipping {src_path} (not found)")
            continue
            
        # 复制为新文件
        new_filename = f"AI_KPOP_RB_{i+1}.mp3"
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
            duration = analysis.get('duration', 180)
            
            print(f"\nProcessing with Smart Logic: {src['title']}")
            
            # 【关键】从 Rekordbox 获取网格信息
            rb_anchor, rb_bpm = get_rekordbox_anchor(src['db_id'])
            
            bpm = rb_bpm if rb_bpm else analysis.get('bpm', 120)
            anchor = rb_anchor if rb_anchor is not None else 0.0
            
            # 【大脑级调用】
            raw_cues = generate_hotcues(
                new_path,
                bpm=bpm,
                duration=duration,
                structure=data
            )
            # 注入手动传入的准确 anchor
            raw_cues['anchor'] = anchor 
            
            # 转换为 Rekordbox 格式
            rb_cues = hotcues_to_rekordbox_format(raw_cues)
            
            # 添加到 XML
            track = xml.add_track(new_path)
            track.set("Name", f"!! {src['title']} (RB Grid) !!")
            track.set("Artist", "AI Pro Cueing (RB)")
            track.set("AverageBpm", bpm)
            track.set("TotalTime", int(duration))
            track.set("Tonality", analysis.get('key', '1A'))
            
            # 使用 Rekordbox 的 anchor 作为 Inizio
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
        pl = xml.add_playlist("!!! AI_KPOP_3_RB_GRID !!!")
        for t in test_tracks:
            pl.add_track(t.TrackID)
        
        xml.save(out_xml)
        print(f"\n[SUCCESS] K-Pop 3 Track RB Grid Test XML: {out_xml}")
    else:
        print("Error: No tracks processed.")

if __name__ == "__main__":
    test_kpop_3_tracks_rb_grid()
