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

# 尝试自动定位项目根目录来修复导入
import typing
PARENT_DIR = Path(__file__).resolve().parent.parent.parent # d:/anti/
if (PARENT_DIR / "core").exists():
    sys.path.insert(0, str(PARENT_DIR))
    sys.path.insert(0, str(PARENT_DIR / "core"))
    sys.path.insert(0, str(PARENT_DIR / "core" / "rekordbox-mcp"))

# 【Phase 12】V12.0 Singularity Entrance
import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "skills"))

from bridge import SkillBridge
sys.path.insert(0, str(PARENT_DIR / "core" / "rekordbox-mcp"))

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from rekordbox_mcp.models import SearchOptions
    # from skills.mashup_intelligence.scripts.core import MashupIntelligence # Removed as per instruction
    from core.config_loader import load_dj_rules
except ImportError as e:
    print(f"❌ 导入失败 (Import failed): {e}")
    print(f"DEBUG Path: {sys.path}")
    sys.exit(1)

def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

async def recommend_for_track(query: str, playlists: List[str], threshold: float = 80.0, vocal_only: bool = True):
    print(f"🚀 [最强大脑] 正在为 {query} 寻找全球最精锐的 3 个 Mashup 组合...")
    print(f"🚀 AI DJ 单曲匹配引擎 (Single-Track Matcher) - 目标: {query}")
    print(f"模式: {'重点人声 (Vocal Only)' if vocal_only else '全维度 (All)'}")
    print(f"{'='*60}")

    db = RekordboxDatabase()
    await db.connect()
    
    # 1. 查找目标单曲 (全库搜索)
    print("🔎 正在全库搜索目标歌曲...")
    search_results = await db.search_tracks(SearchOptions(query=query, limit=10))
    target_track = search_results[0] if search_results else None
    
    if not target_track:
        print(f"❌ 错误: 全库扫描后仍未找到包含 '{query}' 的歌曲。")
        await db.disconnect()
        return

    print(f"✨ 在库中成功定位: {target_track.artist} - {target_track.title}")

    # 2. 准备候选池 (Candidates)
    candidate_tracks = []
    
    if "GLOBAL" in [name.upper() for name in playlists]:
        print("🌐 开启全库扫描模式 (Global Search)...")
        # 直接获取所有活跃音轨
        # 注意：RekordboxDatabase 没有直接获取全库的方法，我们通过 search_tracks(query="", limit=1000) 模拟
        candidate_tracks = await db.search_tracks(SearchOptions(query="", limit=1000))
        print(f"✅ 全库数据加载完成: {len(candidate_tracks)} 首音轨")
    else:
        all_playlists = await db.get_playlists()
        print(f"📚 正在由 {len(playlists)} 个播放列表构建候选池...")
        for pl_name in playlists:
            pl_obj = next((p for p in all_playlists if pl_name.lower() in p.name.lower()), None)
            if pl_obj:
                p_tracks = await db.get_playlist_tracks(pl_obj.id)
                candidate_tracks.extend(p_tracks)
                print(f"✅ 已加载: {pl_obj.name} ({len(p_tracks)} 首)")

    if not candidate_tracks:
        print("❌ 错误: 未能在指定播放列表中加载任何音轨。")
        await db.disconnect()
        return

    # 去重
    seen_ids = set()
    unique_candidates = []
    for t in candidate_tracks:
        if t.id not in seen_ids:
            unique_candidates.append(t)
            seen_ids.add(t.id)
    candidates = unique_candidates # Renamed for clarity in report section

    # 3. 准备数据
    from core.cache_manager import load_cache
    cache = load_cache()
    
    target_ana_entry = cache.get(target_track.file_path)
    target_analysis = target_ana_entry.get('analysis', {}) if target_ana_entry else {'bpm': target_track.bpm, 'key': target_track.key, 'vocal_ratio': 0.5}
    
    target_data = {
        'track_info': {'id': target_track.id, 'title': target_track.title, 'artist': target_track.artist, 'file_path': target_track.file_path},
        'analysis': target_analysis
    }

    # 准备候选池分析数据
    analyzed_candidates = []
    skipped_count = 0
    
    # [V8.0] 专家身份过滤词
    BLACKLIST_TAGS = ["techno", "acid", "minimal", "progressive", "deep house", "trance", "instrumental"]
    WHITELIST_GENRES = ["pop", "k-pop", "hip hop", "r&b", "rap", "c-pop", "remix", "dance"]

    for t in unique_candidates:
        if t.id == target_track.id or t.file_path == target_track.file_path:
            continue
        
        genre = str(t.genre or "").lower()
        title = str(t.title or "").lower()
        
        # 核心过滤：Vibe Archetype (人声/流行/Remix 优先)
        is_pop_remix = any(g in genre for g in WHITELIST_GENRES) or "remix" in title
        is_pure_electronic = any(g in genre for g in BLACKLIST_TAGS)
        
        if vocal_only:
            ana_entry = cache.get(t.file_path)
            analysis = ana_entry.get('analysis', {}) if ana_entry else {}
            v_ratio = analysis.get('vocal_ratio', 0.5)
            
            # 如果开启了人声模式，同时过滤掉纯电子或低人声比例
            if is_pure_electronic or (not is_pop_remix and v_ratio < 0.4):
                skipped_count += 1
                continue
        
        # 基础数据提取
        ana_entry = cache.get(t.file_path)
        analysis = ana_entry.get('analysis', {}) if ana_entry else {'bpm': t.bpm, 'key': t.key, 'vocal_ratio': 0.5}
        
        analyzed_candidates.append({
            'track_info': {'id': t.id, 'title': t.title, 'artist': t.artist, 'file_path': t.file_path, 'genre': t.genre},
            'analysis': analysis
        })

    if vocal_only:
        print(f"🎙️ 流行/人声过滤: 已跳过 {skipped_count} 首不符合“作品感”的音轨。")

    # 4. 计算分数
    # mi = MashupIntelligence() # Removed as per instruction
    matches = []
    print(f"🔎 正在对 {len(analyzed_candidates)} 首候选曲目执行 Mashup 审计...")
    
    for candidate in analyzed_candidates:
        # 【V14.1 Fix】始终使用 mashup_discovery 模式，确保完整 11 维度分析
        score, details = SkillBridge.execute("calculate-mashup", track1=target_data, track2=candidate, mode='mashup_discovery')
        
        if score >= threshold:
            matches.append({'score': score, 'details': details, 'track1': target_data, 'track2': candidate})
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # 4. 生成报告
    from datetime import datetime
    generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 【V19.5 Deep Vibe Search】挖掘前 30 名以寻找非 Pop 选项
    elite_matches = matches[:30]
    match_count = len(elite_matches)
    
    # 清理文件名
    clean_name = "".join([c for c in query if c.isalpha() or c.isdigit() or c==' ' or c=='_']).strip()
    report_path = Path(f"D:/生成的set\search{clean_name}_MASHUP_RECOMMENDATIONS.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Mashup 最强大脑精选报告: {target_track.title}\n\n")
        f.write(f"## 0. 审计概览 (Audit Overview)\n")
        f.write(f"> **目标歌曲**: {target_track.artist} - {target_track.title}\n")
        f.write(f"> **基础数据**: BPM: {target_track.bpm} | Key: {target_track.key}\n\n")
        
        is_global = "GLOBAL" in [name.upper() for name in playlists]
        f.write(f"### 🔍 搜索范围\n")
        f.write(f"- {'🌐 **全库比对 (Global Scan)**: 已执行' if is_global else '📚 **局部比对**: ' + ', '.join(playlists)}\n")
        f.write(f"- **候选音轨总数**: {len(candidates)} 首\n")
        f.write(f"- **11维度审计结果**: 已从 {len(matches)} 个及格选项中精选出 Top 3 黄金组合。\n")
        f.write(f"- **生成时间**: {generation_time}\n\n")
        
        f.write("### 💎 Elite Top 3 黄金组合列表\n")
        f.write("> 以下推荐均基于物理对齐、文化 DNA 及 Stems 对称性深度比对得出。\n\n")
        
        if not elite_matches:
            f.write("⚠️ 未找到合适的高分匹配。\n")
        else:
            for idx, m in enumerate(elite_matches):
                cand = m['track2']['track_info']
                cand_ana = m['track2']['analysis']
                
                f.write(f"### {idx+1}. [{m['score']:.1f}] vs {cand['title']}\n")
                f.write(f"**Candidate**: {cand['artist']} - {cand['title']}\n")
                
                # 数据证据块 (Evidence Block)
                f.write(f"#### 📊 数据证据 (Technical Evidence)\n")
                f.write(f"| 特征 | 目标歌曲 ({target_track.title}) | 候选歌曲 ({cand['title']}) | 匹配结论 |\n")
                f.write(f"| :--- | :--- | :--- | :--- |\n")
                f.write(f"| **BPM** | {target_track.bpm} | {cand_ana.get('bpm')} | {m['details'].get('bpm_tier')} |\n")
                f.write(f"| **Key** | {target_track.key} | {cand_ana.get('key')} | {m['details'].get('key_match', 'Harmonic Neighbor')} |\n")
                f.write(f"| **Stems** | Vocal/Pop | {cand_ana.get('vocal_ratio', 0.5)} | {m['details'].get('mashup_pattern')} |\n\n")
                
                f.write(f"#### 🧠 11维度审计明细 (Audit Details)\n")
                for k, v in m['details'].items():
                    if k in ['score', 'bpm_tier', 'mashup_pattern', 'key_match']: continue
                    f.write(f"- **{k.replace('_', ' ').capitalize()}**: {v}\n")
                
                # 提取模式建议
                p_pattern = m['details'].get('mashup_pattern', 'Free Stem Mix')
                f.write(f"\n> 💡 **专家点评**: 该组合呈现出专业的 `{p_pattern}` 潜力。")
                if "Vocal Alternation" in p_pattern:
                    f.write(" 建议使用乐句接龙模式处理双人声切换。")
                f.write("\n\n---\n\n")

    await db.disconnect()
    
    print(f"\n🎉 匹配完成！已找到 {len(matches)} 个潜在组合。")
    print(f"📝 报告已生成至: {report_path}")
    print(f"{'='*60}\n")
    
    # 自动打开
    try:
        os.startfile(str(report_path))
    except:
        pass

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

    # 3. 联动 SkillBridge 进行矩阵对比
    matches = []
    
    print(f"🔎 正在执行 {len(analyzed_tracks) * (len(analyzed_tracks)-1) // 2} 次维度冲突审计...")
    
    for i in range(len(analyzed_tracks)):
        for j in range(i + 1, len(analyzed_tracks)):
            t1 = analyzed_tracks[i]
            t2 = analyzed_tracks[j]
            
            score, details = SkillBridge.execute("calculate-mashup", track1=t1, track2=t2, mode='mashup_discovery')
            
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
                guide_text = f"“{t1['title']}” x “{t2['title']}” 具有极佳的 Mashup 潜力。"
                f.write(f"> {guide_text}\n")
                f.write("\n---\n\n")

    await db.disconnect()
    
    print(f"\n🎉 推荐完成！发现 {len(matches)} 个极品组合。")
    print(f"📝 报告已生成至: {report_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI DJ Mashup Recommender")
    parser.add_argument("--playlist", type=str, default="House", help="Candidate Pool (Comma separated for multiple)")
    parser.add_argument("--playlists", type=str, help="Alias for --playlist")
    parser.add_argument("--threshold", type=float, default=70.0, help="Mashup score threshold")
    parser.add_argument("--query", type=str, help="Search for a specific track to find matches for")
    parser.add_argument("--vocal-only", action="store_true", help="Only match candidates with high vocal ratio (>0.4)")
    parser.add_argument("--global-scan", action="store_true", help="Scan the entire library instead of specific playlists")
    
    args = parser.parse_args()
    
    if args.global_scan:
        pl_list = ["GLOBAL"]
    else:
        target_pls = args.playlists or args.playlist
        pl_list = [p.strip() for p in target_pls.split(",")]
    
    if args.query:
        asyncio.run(recommend_for_track(args.query, pl_list, args.threshold, vocal_only=args.vocal_only))
    else:
        asyncio.run(recommend_mashups(pl_list[0], args.threshold)) # 批量列表支持主页暂不改动
