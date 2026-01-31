#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按时间顺序分析用户标点习惯"""

from pyrekordbox import Rekordbox6Database
from pyrekordbox.anlz import AnlzFile
from collections import defaultdict
import os
import warnings
warnings.filterwarnings("ignore")

# Rekordbox Phrase Kind 映射
PHRASE_KINDS = {
    1: 'Intro',
    2: 'Up',
    3: 'Down',
    4: 'Chorus',
    5: 'Outro',
    6: 'Verse',
    7: 'Bridge',
    8: 'Breakdown',
    9: 'Buildup',
    10: 'Outro'
}

db = Rekordbox6Database()
contents = list(db.get_content())
cues = list(db.get_cue())

# 建立 ContentID -> Cues 映射
content_cues = defaultdict(list)
for cue in cues:
    d = cue.to_dict()
    content_id = d.get("ContentID")
    in_msec = d.get("InMsec") or 0
    if content_id and in_msec > 0:
        content_cues[content_id].append({
            "msec": in_msec,
            "sec": in_msec / 1000.0,
            "comment": d.get("Comment") or ""
        })

# 只保留有 4 个或以上标点的歌曲
valid_songs = {k: v for k, v in content_cues.items() if len(v) >= 4}
print(f"有 4+ 个标点的歌曲: {len(valid_songs)} 首")

# 建立 ContentID -> Content 映射
content_map = {c.ID: c for c in contents}

# USBANLZ 基础目录
anlz_base = r'C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\USBANLZ'

# 统计变量
stats = defaultdict(int)

# 详细样本
samples = []

# 遍历有效歌曲
count = 0
for content_id, cue_list in valid_songs.items():
    content = content_map.get(content_id)
    if not content:
        continue
    
    # 获取 BPM
    bpm = (content.BPM or 12800) / 100.0
    duration = content.Length or 300
    
    # 按时间排序
    cue_list_sorted = sorted(cue_list, key=lambda x: x["sec"])
    
    # 第一个标点作为 A，第二个作为 B
    # 倒数第二个作为 C，倒数第一个作为 D
    a_sec = cue_list_sorted[0]["sec"]
    b_sec = cue_list_sorted[1]["sec"]
    c_sec = cue_list_sorted[-2]["sec"]
    d_sec = cue_list_sorted[-1]["sec"]
    
    # 尝试读取分析文件
    uuid = content.UUID
    if not uuid:
        continue
    
    prefix = uuid[:3]
    suffix = uuid[3:]
    anlz_dir = os.path.join(anlz_base, prefix, f"{suffix}")
    ext_path = os.path.join(anlz_dir, "ANLZ0000.EXT")
    
    phrases = []
    if os.path.exists(ext_path):
        try:
            anlz = AnlzFile.parse_file(ext_path)
            for tag in anlz.tags:
                if tag.type == "PSSI":
                    for entry in tag.content.entries:
                        beat = entry.beat
                        kind = entry.kind
                        kind_name = PHRASE_KINDS.get(kind, f"Unknown({kind})")
                        beat_duration = 60.0 / bpm if bpm > 0 else 0.5
                        time_sec = beat * beat_duration
                        phrases.append({
                            "beat": beat,
                            "time": time_sec,
                            "kind": kind_name
                        })
        except:
            pass
    
    if not phrases:
        continue
    
    # 找到每个标点对应的段落
    def find_phrase_at(time_sec, phrases):
        for i, p in enumerate(phrases):
            if i < len(phrases) - 1:
                if phrases[i]["time"] <= time_sec < phrases[i+1]["time"]:
                    return p["kind"]
            else:
                if phrases[i]["time"] <= time_sec:
                    return p["kind"]
        return phrases[0]["kind"] if phrases else "Unknown"
    
    a_phrase = find_phrase_at(a_sec, phrases)
    b_phrase = find_phrase_at(b_sec, phrases)
    c_phrase = find_phrase_at(c_sec, phrases)
    
    # 计算间距
    beat_duration = 60.0 / bpm
    ab_beats = (b_sec - a_sec) / beat_duration
    cd_beats = (d_sec - c_sec) / beat_duration
    
    # 统计
    stats["total"] += 1
    stats[f"a_{a_phrase}"] += 1
    stats[f"b_{b_phrase}"] += 1
    stats[f"c_{c_phrase}"] += 1
    
    # 间距统计
    if 28 <= ab_beats <= 36:
        stats["ab_8bars"] += 1
    elif 56 <= ab_beats <= 72:
        stats["ab_16bars"] += 1
    elif 12 <= ab_beats <= 20:
        stats["ab_4bars"] += 1
    
    if 28 <= cd_beats <= 36:
        stats["cd_8bars"] += 1
    elif 56 <= cd_beats <= 72:
        stats["cd_16bars"] += 1
    
    # 保存样本
    if len(samples) < 15:
        samples.append({
            "title": content.Title[:35],
            "bpm": bpm,
            "duration": duration,
            "a_sec": round(a_sec, 2),
            "a_phrase": a_phrase,
            "b_sec": round(b_sec, 2),
            "b_phrase": b_phrase,
            "c_sec": round(c_sec, 2),
            "c_phrase": c_phrase,
            "d_sec": round(d_sec, 2),
            "ab_beats": round(ab_beats, 1),
            "cd_beats": round(cd_beats, 1),
            "num_cues": len(cue_list)
        })
    
    count += 1
    if count >= 300:
        break

# 输出结果
total = stats["total"] or 1
print("=" * 70)
print("用户标点习惯全量审计报告")
print("=" * 70)
print(f"\n成功分析歌曲数: {stats['total']}")

print("\n" + "=" * 50)
print("第一个标点 (Mix-In 起点) 落在哪个段落")
print("=" * 50)
for key in ["a_Intro", "a_Up", "a_Down", "a_Verse", "a_Buildup", "a_Chorus"]:
    if stats[key] > 0:
        print(f"  {key.replace('a_', ''):<12}: {stats[key]:3d} ({100*stats[key]/total:5.1f}%)")

print("\n" + "=" * 50)
print("第二个标点 (Mix-In 完成/能量点) 落在哪个段落")
print("=" * 50)
for key in ["b_Intro", "b_Up", "b_Down", "b_Buildup", "b_Chorus", "b_Breakdown"]:
    if stats[key] > 0:
        print(f"  {key.replace('b_', ''):<12}: {stats[key]:3d} ({100*stats[key]/total:5.1f}%)")

print("\n" + "=" * 50)
print("倒数第二个标点 (Mix-Out 起点) 落在哪个段落")
print("=" * 50)
for key in ["c_Outro", "c_Buildup", "c_Chorus", "c_Down", "c_Up"]:
    if stats[key] > 0:
        print(f"  {key.replace('c_', ''):<12}: {stats[key]:3d} ({100*stats[key]/total:5.1f}%)")

print("\n" + "=" * 50)
print("前两个标点间距 (Mix-In 窗口)")
print("=" * 50)
print(f"  约 4 bars (12-20 beats):  {stats['ab_4bars']:3d} ({100*stats['ab_4bars']/total:5.1f}%)")
print(f"  约 8 bars (28-36 beats):  {stats['ab_8bars']:3d} ({100*stats['ab_8bars']/total:5.1f}%)")
print(f"  约 16 bars (56-72 beats): {stats['ab_16bars']:3d} ({100*stats['ab_16bars']/total:5.1f}%)")

print("\n" + "=" * 50)
print("最后两个标点间距 (Mix-Out 窗口)")
print("=" * 50)
print(f"  约 8 bars (28-36 beats):  {stats['cd_8bars']:3d} ({100*stats['cd_8bars']/total:5.1f}%)")
print(f"  约 16 bars (56-72 beats): {stats['cd_16bars']:3d} ({100*stats['cd_16bars']/total:5.1f}%)")

print("\n" + "=" * 70)
print("典型样本")
print("=" * 70)
for s in samples:
    print(f"\n【{s['title']}】 BPM: {s['bpm']:.0f} | {s['num_cues']} 个标点")
    print(f"  1st: {s['a_sec']:6.2f}s [{s['a_phrase']:<10}]")
    print(f"  2nd: {s['b_sec']:6.2f}s [{s['b_phrase']:<10}] (间距: {s['ab_beats']:.0f} beats = {s['ab_beats']/4:.1f} bars)")
    print(f"  -2:  {s['c_sec']:6.2f}s [{s['c_phrase']:<10}]")
    print(f"  -1:  {s['d_sec']:6.2f}s              (间距: {s['cd_beats']:.0f} beats = {s['cd_beats']/4:.1f} bars)")
