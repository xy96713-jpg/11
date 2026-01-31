import sys
import os
import json
from pathlib import Path

# 设置导入路径
BASE_DIR = Path(r"d:\anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))

from strict_bpm_multi_set_sorter import deep_analyze_track
from enhanced_harmonic_set_sorter import get_key_compatibility_flexible, get_bpm_compatibility_flexible, load_cache, ANALYZER_VERSION

def analyze_and_suggest():
    file_path = r"C:\Users\Administrator\Downloads\极品贵公子,1CEKary艾斯凯瑞 - OD妹.mp3"
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return

    # 1. 分析目标歌曲
    print(f"--- 正在分析: {os.path.basename(file_path)} ---")
    target_res = deep_analyze_track(file_path)
    if not target_res:
        print("Error: Analysis failed.")
        return
    
    bpm = target_res.get('bpm', 120)
    key = target_res.get('key', '1A')
    artist = "1CEKary艾斯凯瑞"
    title = "OD妹"
    
    print(f"目标属性: BPM={bpm:.1f}, Key={key}, Artist={artist}")

    # 2. 搜寻候选匹配
    cache = load_cache()
    candidates = []
    
    for h, entry in cache.items():
        analysis = entry.get('analysis')
        if not analysis: continue
        
        c_file = entry.get('file_path', '')
        if not os.path.exists(c_file) or file_path == c_file: continue
        
        c_bpm = analysis.get('bpm', 120)
        c_key = analysis.get('key', '1A')
        
        # 基本过滤：BPM 差异在 8 以内 (适应 Mashup)
        bpm_diff = abs(bpm - c_bpm)
        if bpm_diff > 8: continue
        
        # 调性兼容性
        key_score = get_key_compatibility_flexible(key, c_key)
        if key_score < 60: continue
        
        # 计算综合匹配分 (此处简化，不调用复杂的 NarrativePlanner 以免环境不匹配)
        total_score = key_score * 0.6 + (10 - bpm_diff) * 4
        
        candidates.append({
            "title": os.path.basename(c_file),
            "bpm": c_bpm,
            "key": c_key,
            "score": total_score,
            "artist": analysis.get('artist', 'Unknown')
        })

    # 排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n--- 为 '{title}' 推荐的 Mashup 伴侣 (Top 10) ---")
    for i, c in enumerate(candidates[:10], 1):
        print(f"{i}. {c['title']} | Score: {c['score']:.1f} | BPM: {c['bpm']:.1f} | Key: {c['key']}")

if __name__ == "__main__":
    analyze_and_suggest()
