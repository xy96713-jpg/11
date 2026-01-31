import json
import os
from pathlib import Path

cache_path = Path(r"d:\anti\song_analysis_cache.json")

def audit_cache():
    if not cache_path.exists():
        print("Cache not found.")
        return

    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    total = len(cache)
    v3_count = 0
    ghost_count = 0
    missing_analysis = 0

    for k, v in cache.items():
        fp = v.get('file_path')
        if not fp or not os.path.exists(fp):
            ghost_count += 1
            continue
            
        analysis = v.get('analysis', {})
        if not analysis:
            missing_analysis += 1
            continue
            
        # 检查 V3 特征
        if "spectral_bands" in analysis and "swing_dna" in analysis:
            v3_count += 1

    print(f"--- 缓存系统审计报告 ---")
    print(f"1. 缓存条目总量: {total}")
    print(f"2. V3-PRO 覆盖率: {v3_count}/{total} ({(v3_count/total*100):.1f}%)")
    print(f"3. 幽灵条目 (文件缺失): {ghost_count}")
    print(f"4. 损坏条目 (缺少分析): {missing_analysis}")
    print(f"------------------------")

if __name__ == "__main__":
    audit_cache()
