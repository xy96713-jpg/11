import asyncio
import sys
import json
from pathlib import Path

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase
from skills.mashup_intelligence.scripts.core import MashupIntelligence
from core.cache_manager import load_cache

# 模拟 Harmonic Score
def harmonic_compatibility(k1, k2):
    if not k1 or not k2: return 50
    if k1 == k2: return 100
    # 简化逻辑
    return 80

async def main():
    db = RekordboxDatabase()
    await db.connect()
    
    # 获取全部曲目
    all_ts = await db.get_most_played_tracks(limit=5000)
    
    # 【核心筛选】只保留“刚刚导入”的新专辑音轨
    core_tracks = []
    for t in all_ts:
        title_lower = (t.title or "").lower()
        file_lower = (t.file_path or "").lower()
        album_lower = (t.album or "").lower()
        
        # 严格限定：必须包含 XG 且 (文件名带 p 或 专辑是 the core)
        is_new_album = ("p" in t.title[:4].lower() and "xg" in title_lower) or ("the core" in album_lower)
        
        if is_new_album:
            core_tracks.append(t)
            
    print(f"Found {len(core_tracks)} tracks specifically from THE CORE.")

    cache = load_cache()
    path_map = {v.get('file_path', '').replace('\\', '/'): v for v in cache.values()}
    
    tracks = []
    for t in core_tracks:
        path = t.file_path.replace('\\', '/')
        entry = path_map.get(path, {})
        analysis = entry.get('analysis', entry)
        
        bpm = analysis.get('bpm', t.bpm)
        key = analysis.get('key', t.key)
        
        # 【修正】处理 BPM 解析错误
        # p9 4 SEASONS 被识别为 176 (Double Time)，实际是 88 (慢歌)
        is_slow = False
        if "4 SEASONS" in t.title.upper():
            is_slow = True
        elif bpm and bpm < 90:
            is_slow = True
        elif bpm and bpm > 170: # 可能是 85-90 的慢歌被误判为 170-180
            print(f"Suspected slow track (High BPM detected as slow vibe): {t.title}")
            # 专辑内 ROCK THE BOAT 192 是快歌，4 SEASONS 是慢歌
            if "4 SEASONS" in t.title.upper(): is_slow = True

        if is_slow:
            print(f"Skipping slow track: {t.title}")
            continue
            
        tracks.append({
            'title': t.title,
            'bpm': bpm,
            'key': key or "8A",
            'file_path': t.file_path
        })

    if not tracks:
        print("No dance tracks found in the new album!")
        await db.disconnect()
        return

    # 用户强制：HYPNOTIZE 第一
    ordered = []
    first = next((t for t in tracks if "HYPNOTIZE" in t['title'].upper()), None)
    if first:
        ordered.append(first)
        tracks.remove(first)
    else:
        ordered.append(tracks.pop(0))

    # 排序逻辑：BPM 阶梯 + Key 兼容
    while tracks:
        curr = ordered[-1]
        best_cand = None
        best_score = -1000
        
        for cand in tracks:
            # 权重：BPM 40% + Key 60%
            bpm_diff = abs(curr['bpm'] - cand['bpm'])
            bpm_score = 40 * (1.0 - bpm_diff / 100.0)
            
            key_score = 0
            if curr['key'] == cand['key']: key_score = 60
            elif cand['key'] in [curr['key'][:-1]+'B' if curr['key'][-1]=='A' else curr['key'][:-1]+'A']: key_score = 40
            
            total = bpm_score + key_score
            if total > best_score:
                best_score = total
                best_cand = cand
        
        if best_cand:
            ordered.append(best_cand)
            tracks.remove(best_cand)
        else:
            break

    # 输出 MD
    report_path = Path("d:/anti/xg_core_set.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# XG - THE CORE 新专辑 舞曲 Set 排列建议 (修正版)\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **纯净模式 V2**：已剔除慢歌 `4 SEASONS`。基于 **BPM 阶梯** 和 **Harmonic Key** 线性排列。\n\n")
        f.write("| 顺序 | 曲目名称 | BPM | Key | 混音建议 |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        for i, t in enumerate(ordered):
            tip = "---"
            if i > 0:
                prev = ordered[i-1]
                if prev['key'] == t['key']: tip = "🎯 Perfect Key Match"
                elif abs(prev['bpm'] - t['bpm']) < 3: tip = "⚡ BPM Sync Mix"
                elif abs(prev['bpm'] - t['bpm']) > 40: tip = "🌀 Double/Half Time"
            
            f.write(f"| {i+1} | {t['title']} | {t['bpm']} | {t['key']} | {tip} |\n")

    print(f"✅ Final Set Generated: {report_path}")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
