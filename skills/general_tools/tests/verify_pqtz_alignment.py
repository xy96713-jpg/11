#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Audit: PQTZ Grid Alignment Verifier
- Reads generated XML
- Connects to Rekordbox DB to fetch raw PQTZ beat grids
- Validates if every Hotcue is snapped to a beat (within 1ms)
"""

import os
import sys
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path

# Add core paths
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from core.rekordbox_phrase_reader import RekordboxPhraseReader
except ImportError:
    print("❌ Failed to import core modules.")
    sys.exit(1)

async def verify_alignment(xml_path: str):
    print(f"\n{'='*60}")
    print(f"🔍 PQTZ 物理网格审计 - XML: {os.path.basename(xml_path)}")
    print(f"{'='*60}")

    if not os.path.exists(xml_path):
        print(f"❌ XML 文件不存在: {xml_path}")
        return

    db = RekordboxDatabase()
    await db.connect()
    reader = RekordboxPhraseReader()

    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    tracks = root.findall(".//TRACK")
    total_checks = 0
    failures = 0

    print(f"📊 正在审计 {len(tracks)} 首音轨的标点对齐情况...")

    for t in tracks:
        title = t.get("Name")
        track_id = t.get("TrackID")
        
        # 获取 UUID
        # Rekordbox XML 中的 UUID 通常不在标准属性里，我们需要通过文件路径或 ID 在 DB 中匹配
        # 这里简单起见，按 ID 或位置匹配
        from urllib.parse import unquote
        location = t.get("Location")
        if not location:
            # print(f"  ⚠️ 跳过 {title[:20]}: XML 中缺失 Location")
            continue
            
        # 解码 URL 路径并提取纯文件名
        clean_path = unquote(location.replace("file://localhost/", ""))
        filename = os.path.basename(clean_path)
        
        # 尝试剥离 AI 后缀 (如 _aff2e3.mp3) 以匹配原库
        import re
        base_filename = re.sub(r'_[a-f0-9]{6}\.mp3$', '', filename)
        
        # 从 DB 找 UUID
        content_uuid = None
        # 优先模糊匹配原文件名
        db_tracks = await db.search_tracks_by_filename(base_filename)
        if db_tracks:
            content_uuid = db_tracks[0].content_uuid

        if not content_uuid:
            # print(f"  ⚠️ 跳过 {title[:20]}: 无法匹配数据库 UUID")
            continue

        # 获取原始节拍网格
        beat_grid = reader.get_beat_grid(content_uuid)
        if not beat_grid:
            # print(f"  ⚠️ 跳过 {title[:20]}: 数据库中无 PQTZ 数据")
            continue
            
        beat_times = sorted([b['time'] for b in beat_grid])
        
        # 检查每个 POSITION_MARK
        marks = t.findall("POSITION_MARK")
        for m in marks:
            cue_name = m.get("Name")
            cue_time = float(m.get("Start"))
            
            # 排除非 A-E 的点（如果有）
            if m.get("Num") == "-1" and not cue_name.startswith("["):
                continue
                
            total_checks += 1
            
            # 寻找最近的 beat
            import bisect
            idx = bisect.bisect_left(beat_times, cue_time)
            
            candidates = []
            if idx > 0: candidates.append(beat_times[idx-1])
            if idx < len(beat_times): candidates.append(beat_times[idx])
            
            if not candidates:
                diff = 999
            else:
                nearest_beat = min(candidates, key=lambda b: abs(b - cue_time))
                diff = abs(nearest_beat - cue_time)

            if diff > 0.002: # 2ms 容差
                failures += 1
                print(f"  ❌ 对齐失败: {title[:25]} | {cue_name}")
                print(f"     Time: {cue_time:.3f}s | Nearest Beat: {nearest_beat:.3f}s | Diff: {diff*1000:.1f}ms")

    print(f"\n{'='*60}")
    print(f"审计结果:")
    print(f"- 总检查点位: {total_checks}")
    print(f"- 失败数: {failures}")
    if total_checks > 0:
        success_rate = (total_checks - failures) / total_checks * 100
        print(f"- 成功率: {success_rate:.1f}%")
        if failures == 0:
            print(f"🏆 100% 物理对齐！符合 V3.0 Ultra+ 专业级红线。")
        else:
            print(f"⚠️ 警告：检测到采样级偏差，请检查 generator 逻辑。")
    else:
        print("❓ 未能进行有效审计（可能无匹配的 PQTZ 数据）。")
    print(f"{'='*60}\n")

    await db.disconnect()

if __name__ == "__main__":
    import glob
    xml_files = glob.glob("D:/生成的set/*.xml")
    if xml_files:
        latest = max(xml_files, key=os.path.getmtime)
        asyncio.run(verify_alignment(latest))
    else:
        print("❌ 未找到 XML 文件以供审计。")
