#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI DJ Mashup Recommender (V4 Core)
- 11-Dimension Scoring System Integration
- Rekordbox Playlist Scanning
- Professional Stems Execution Guide
"""

import os
import sys
import asyncio
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

# 添加核心库路径支持
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from skills.mashup_intelligence.scripts.core import MashupIntelligence
    from core.config_loader import load_dj_rules
    from core.unified_brain import UnifiedBrain
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

async def recommend_mashups(playlist_name: str, threshold: float = 75.0, top_n: int = 15):
    print(f"\n{'='*60}")
    print(f"🚀 AI DJ Mashup 推荐引擎 - 正在扫描: {playlist_name}")
    print(f"{'='*60}")

    db = RekordboxDatabase()
    await db.connect()
    
    # 1. 查找播放列表
    all_playlists = await db.get_playlists()
    target_pl = next((p for p in all_playlists if p.name == playlist_name), None)
    
    if not target_pl:
        # 尝试模糊匹配
        target_pl = next((p for p in all_playlists if playlist_name.lower() in p.name.lower()), None)
        
    if not target_pl:
        print(f"❌ 错误：找不到播放列表 '{playlist_name}'")
        await db.disconnect()
        return

    print(f"✅ 已找到播放列表: {target_pl.name} ({target_pl.track_count} 首音轨)")
    
    # 2. 获取音轨及分析数据
    tracks = await db.get_playlist_tracks(target_pl.id)
    
    from core.cache_manager import load_cache
    cache = load_cache()
    
    analyzed_tracks = []
    print(f"🧠 正在从缓存提取音频特征与 DNA 数据...")
    for t in tracks:
        # 尝试从缓存获取分析数据
        analysis = cache.get(t.file_path)
        if not analysis:
            # 如果没有，尝试进行轻量级适配（基于数据库元数据）
            analysis = {
                'bpm': t.bpm,
                'key': t.key,
                'vocal_ratio': 0.5, # 默认
                'energy': t.rating * 20 if t.rating else 50,
                'file_path': t.file_path,
                'tags': []
            }
        else:
            # 兼容性处理：如果缓存里有 analysis 字典，直接用它的内容
            if 'analysis' in analysis:
                analysis = analysis['analysis']
        
        analyzed_tracks.append({
            'track_info': {
                'id': t.id,
                'title': t.title,
                'artist': t.artist,
                'file_path': t.file_path
            },
            'analysis': analysis
        })

    # 3. 联动 Mashup Intelligence 进行矩阵对比
    mi = MashupIntelligence()
    matches = []
    
    print(f"🔎 正在执行 {len(analyzed_tracks) * (len(analyzed_tracks)-1) // 2} 次维度冲突审计...")
    
    for i in range(len(analyzed_tracks)):
        for j in range(i + 1, len(analyzed_tracks)):
            t1 = analyzed_tracks[i]
            t2 = analyzed_tracks[j]
            
            score, details = mi.calculate_mashup_score(t1, t2, mode='mashup_discovery')
            
            if score >= threshold:
                matches.append({
                    'score': score,
                    'details': details,
                    'track1': t1,
                    'track2': t2
                })

    from datetime import datetime
    generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report_path = Path("D:/生成的set/MASHUP_RECOMMENDATIONS.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Mashup 推荐报告: {playlist_name}\n\n")
        f.write(f"- **总音轨数**: {len(analyzed_tracks)}\n")
        f.write(f"- **匹配对数**: {len(matches)}\n")
        f.write(f"- **推荐门限**: {threshold}\n")
        f.write(f"- **生成时间**: {generation_time}\n\n")
        
        if not matches:
            f.write("⚠️ 未在当前歌单中发现高分 Mashup 组合。\n")
        else:
            for idx, m in enumerate(matches[:top_n]):
                t1 = m['track1']['track_info']
                t2 = m['track2']['track_info']
                
                f.write(f"### {idx+1}. [{m['score']:.1f}] {t1['title']} x {t2['title']}\n")
                f.write(f"**对阵双方**:\n")
                f.write(f"- Deck A: {t1['artist']} - {t1['title']} ({m['track1']['analysis'].get('key')})\n")
                f.write(f"- Deck B: {t2['artist']} - {t2['title']} ({m['track2']['analysis'].get('key')})\n\n")
                
                f.write(f"**多维度评价**:\n")
                for k, v in m['details'].items():
                    f.write(f"- {k.capitalize()}: {v}\n")
                
                f.write(f"\n**[最强大脑 执行脚本]**:\n")
                guide = mi.generate_unified_guide(m['track1'], m['track2'], m['score'], m['details'])
                for g in guide:
                    f.write(f"> {g}\n")
                f.write("\n---\n\n")

    await db.disconnect()
    
    print(f"\n🎉 推荐完成！发现 {len(matches)} 个极品组合。")
    print(f"📝 报告已生成至: {report_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI DJ Mashup Recommender")
    parser.get_default("playlist")
    parser.add_argument("--playlist", type=str, default="House", help="Rekordbox Playlist Name")
    parser.add_argument("--threshold", type=float, default=70.0, help="Mashup score threshold")
    
    args = parser.parse_args()
    
    asyncio.run(recommend_mashups(args.playlist, args.threshold))
