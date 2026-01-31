import json
import os
from pathlib import Path

# 系统路径
CACHE_FILE = r"d:\anti\song_analysis_cache.json"
OUTPUT_DIR = Path(r"D:\生成的set")
OUTPUT_FILE = OUTPUT_DIR / "XG_THE_CORE_HighEnergy_Set.m3u"

# XG 嗨歌候选名单 (基于缓存验证过的标题)
XG_TARGETS = [
    "p2 XG - GALA",
    "p4 XG - TAKE MY BREATH",
    "p5 XG - NO GOOD",
    "p6 XG - HYPNOTIZE",
    "p7 XG - UP NOW"
]

def generate_xg_m3u():
    print("--- [XG-SET] 正在按照 DJ Skill 规则生成 XG 专场 ---")
    
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
        
    # 1. 提取目标音轨信息
    tracks = []
    for keyword in XG_TARGETS:
        for v in cache.values():
            if keyword.upper() in v.get('file_path','').upper():
                a = v['analysis']
                tracks.append({
                    'title': keyword,
                    'path': v['file_path'],
                    'bpm': a['bpm'],
                    'key': a['key'],
                    'energy': a.get('energy', 30)
                })
                break
    
    if not tracks:
        print("Error: No XG tracks found in cache.")
        return

    # 2. 专业排序逻辑 (按照好接好打原则手动微调/或调用部分分析逻辑)
    # 策略：BPM 稳步爬升，调性相邻或相同
    # 目标顺序: 
    # 1. p7 (114.5, 2A) -> 2. p4 (126.0, 2A) [同调性大跨度提速]
    # 3. p5 (125.52, 4B) [2A->4B 是关联调性，且速度回归 125]
    # 4. p6 (128.21, 4A) [4B->4A 是同号大小调切换]
    # 5. p2 (130.72, 11A) [作为 Peak 结尾]
    
    sorted_order = [
         "p6 XG - HYPNOTIZE",
         "p2 XG - GALA",
         "p4 XG - TAKE MY BREATH",
         "p5 XG - NO GOOD",
         "p7 XG - UP NOW"
    ]
    
    final_tracks = []
    for title in sorted_order:
        for t in tracks:
            if title.upper() in t['path'].upper():
                final_tracks.append(t)
                break
                
    # 3. 写入 M3U
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as m3u:
        m3u.write("#EXTM3U\n")
        for t in final_tracks:
            # 增加 DJ 备注
            m3u.write(f"#EXTINF:-1,[{t['key']}] [{round(t['bpm'],1)}] {t['title']}\n")
            m3u.write(f"{t['path'].replace('/', '\\')}\n")
            
    print(f"\n[SUCCESS] M3U 文件已生成: {OUTPUT_FILE}")
    print("\n--- 专家排表建议 ---")
    for i, t in enumerate(final_tracks):
        print(f"{i+1}. {t['title']} | {t['key']} | {round(t['bpm'],1)} BPM")
        if i < len(final_tracks)-1:
            next_t = final_tracks[i+1]
            print(f"   >>> 转场提示: 从 {t['bpm']} 提速至 {next_t['bpm']} | 调性兼容: {t['key']} -> {next_t['key']}")

if __name__ == "__main__":
    generate_xg_m3u()
