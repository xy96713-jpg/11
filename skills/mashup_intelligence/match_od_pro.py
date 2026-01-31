import sys
import os
import json
from pathlib import Path

# 设置导入路径
BASE_DIR = Path(r"d:\anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))

from strict_bpm_multi_set_sorter import deep_analyze_track
from enhanced_harmonic_set_sorter import get_key_compatibility_flexible, load_cache
from narrative_set_planner import NarrativePlanner

def deep_match():
    file_path = r"C:\Users\Administrator\Downloads\极品贵公子,1CEKary艾斯凯瑞 - OD妹.mp3"
    target_res = deep_analyze_track(file_path)
    if not target_res: return
    
    bpm = target_res.get('bpm', 120)
    key = target_res.get('key', '1A')
    
    planner = NarrativePlanner()
    # 设置主题：极品贵公子 / 奢华都市 / 动感
    planner.set_theme("极品贵公子 / 奢华都市精英叙事 / 动感 Afroswing")
    
    cache = load_cache()
    matches = []
    
    for h, entry in cache.items():
        analysis = entry.get('analysis')
        if not analysis: continue
        fp = entry.get('file_path', '')
        if fp == file_path or not os.path.exists(fp): continue
        
        c_bpm = analysis.get('bpm', 120)
        c_key = analysis.get('key', '1A')
        
        # 严格过滤
        if abs(bpm - c_bpm) > 10: continue
        key_score = get_key_compatibility_flexible(key, c_key)
        if key_score < 60: continue
        
        # 叙事分
        nr_score, nr_details = planner.calculate_narrative_score(
            {'artist': '1CEKary艾斯凯瑞', 'title': 'OD妹'},
            {'artist': analysis.get('artist', 'Unknown'), 'title': analysis.get('title', os.path.basename(fp))}
        )
        
        total_score = key_score * 0.4 + (20 - abs(bpm-c_bpm)) * 2 + nr_score * 0.4
        
        matches.append({
            "title": analysis.get('title') or os.path.basename(fp),
            "artist": analysis.get('artist', 'Unknown'),
            "bpm": c_bpm,
            "key": c_key,
            "score": total_score,
            "nr_advice": planner.get_narrative_advice(
                {'artist': '1CEKary艾斯凯瑞'},
                {'artist': analysis.get('artist', 'Unknown')}
            )
        })

    matches.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n[OD妹] 深度匹配建议集 (Top 15)")
    print("-" * 80)
    for i, m in enumerate(matches[:15], 1):
        print(f"{i}. {m['artist']} - {m['title']}")
        print(f"   BPM: {m['bpm']:.1f} | Key: {m['key']} | Score: {m['score']:.1f}")
        print(f"   专家建议: {m['nr_advice']}")
        print("-" * 80)

if __name__ == "__main__":
    deep_match()
