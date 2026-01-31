from pyrekordbox.rbxml import RekordboxXml
import os
import shutil
import json
from pathlib import Path

def test_kpop_3_tracks():
    print("=== Testing 3 K-Pop Tracks with Copy Strategy ===")
    
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
    
    output_dir = "D:/生成的set/kpop_test_v1"
    os.makedirs(output_dir, exist_ok=True)
    out_xml = "D:/生成的set/AI_KPOP_3_TEST.xml"
    
    xml = RekordboxXml(name="rekordbox", version="6.0.0", company="Pioneer DJ")
    test_tracks = []
    
    for i, src in enumerate(source_tracks):
        src_path = src['path']
        if not os.path.exists(src_path):
            print(f"Skipping {src_path} (not found)")
            continue
            
        # 复制为新文件，彻底绕过 Rekordbox 缓存
        new_filename = f"AI_KPOP_TEST_{i+1}.mp3"
        new_path = os.path.join(output_dir, new_filename).replace('\\', '/')
        shutil.copy2(src_path, new_path)
        
        # 查找分析
        ref = None
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
            
            # 添加到 XML
            track = xml.add_track(new_path)
            track.set("Name", f"!! {src['title']} !!")
            track.set("Artist", "AI KPOP Test")
            track.set("AverageBpm", bpm)
            track.set("TotalTime", int(duration))
            track.set("Tonality", found_analysis.get('key', '1A'))
            
            # 注入网格
            track.add_tempo(Inizio=0.0, Bpm=bpm, Metro="4/4", Battito=1)
            
            # 注入标点
            a_in = found_analysis.get('mix_in_point', 10.0)
            c_out = found_analysis.get('mix_out_point', duration - 10)
            
            track.add_mark(Name="!! AI_ENTRY_A !!", Type="cue", Start=round(a_in, 3), Num=0)
            track.add_mark(Name="!! AI_TRANS_B !!", Type="cue", Start=round(a_in + (8 * bar_sec), 3), Num=1)
            track.add_mark(Name="!! AI_EXIT_C !!", Type="cue", Start=round(c_out - (8 * bar_sec), 3), Num=2)
            track.add_mark(Name="!! AI_END_D !!", Type="cue", Start=round(c_out, 3), Num=3)
            track.add_mark(Name="!! AI_DROP_E !!", Type="cue", Start=round(found_analysis.get('drop_point', 30.0), 3), Num=4)
            
            test_tracks.append(track)
            print(f"Processed: {src['title']} -> {new_filename}")
        else:
            print(f"No cache for: {src['title']}")

    # 加入播放列表
    if test_tracks:
        pl = xml.add_playlist("!!! AI_KPOP_3_TEST !!!")
        for t in test_tracks:
            pl.add_track(t.TrackID)
        
        xml.save(out_xml)
        print(f"\n[SUCCESS] K-Pop 3 Track Test XML: {out_xml}")
    else:
        print("Error: No tracks processed.")

if __name__ == "__main__":
    test_kpop_3_tracks()
