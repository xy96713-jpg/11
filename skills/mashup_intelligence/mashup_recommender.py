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

async def recommend_for_track(query: str, target_playlist_name: str = "House", threshold: float = 70.0, top_n: int = 20):
    print(f"\n{'='*60}")
    print(f"🚀 AI DJ 单曲匹配引擎 (Single-Track Matcher) - 目标: {query}")
    print(f"{'='*60}")

    db = RekordboxDatabase()
    await db.connect()
    
    # 1. 查找目标单曲
    print("🔎 正在全库搜索目标歌曲...")
    # 获取所有曲目进行搜索 (暂时策略，若库很大应优化 SQL)
    # 这里的 get_playlists 是为了获取上下文，搜索需要更直接的方法
    # 假设 database 提供了 search 类似功能，或者如果没有，我们遍历所有 tracks
    # 由于 API 不确定，我们先获取一个大播放列表作为候选池，或者尝试获取所有
    
    # 尝试在候选池中先找目标，或者使用 specialized search
    # 为了稳健，我们先加载一个默认的大池子 (比如 House)，如果没找到，再警告。
    # 更好的方法是：
    all_tracks = []
    playlists = await db.get_playlists()
    
    # 收集候选池 (Candidates)
    candidate_tracks = []
    target_track = None
    
    # 策略 1: 优先在所有 playlists 中找名为 "search:{query}" 的临时列表 (Sorter 生成的)
    search_pl_obj = next((p for p in playlists if f"search:{query}" in p.name), None)
    
    if search_pl_obj:
        print(f"📚 发现临时搜索列表: {search_pl_obj.name}")
        search_tracks = await db.get_playlist_tracks(search_pl_obj.id)
        if search_tracks:
            target_track = search_tracks[0] # 既然是 search:蛇舞，第一首应该就是
    
    # 策略 2: 如果没找到，再从 target_playlist_name 获取候选池
    if not target_track:
        target_pl_obj = next((p for p in playlists if target_playlist_name.lower() in p.name.lower()), None)
        if not target_pl_obj:
             # Fallback to a large playlist if 'House' not found
             target_pl_obj = playlists[0] if playlists else None
             
        if target_pl_obj:
            print(f"📚 加载候选池: {target_pl_obj.name}...")
            candidate_tracks_pool = await db.get_playlist_tracks(target_pl_obj.id)
            # 在候选池里找目标
            target_track = next((t for t in candidate_tracks_pool if query.lower() in t.title.lower() or query.lower() in t.artist.lower()), None)
            
            # 这里顺便就把 candidate_tracks 填了
            candidate_tracks = candidate_tracks_pool

    # 策略 3: 手动遍历前几个大列表
    if not target_track:
        print(f"⚠️ 候选池 ({target_playlist_name}) 中未找到 '{query}'，尝试扩大搜索...")
        # 简单遍历前几个大列表
        for pl in playlists[:5]:
            if pl.id == target_pl_obj.id: continue
            tracks = await db.get_playlist_tracks(pl.id)
            found = next((t for t in tracks if query.lower() in t.title.lower()), None)
            if found:
                target_track = found
                # 把这些 tracks 也加入 candidate? 不，单曲匹配通常是拿这个单曲去撞库(候选池)
                # 我们保持 candidate_tracks 为 target_pl_obj 的内容（通常是 House/Library）
                break
    
    if not target_track:
        print(f"❌ 错误: 在常用列表中未找到包含 '{query}' 的歌曲。")
        await db.disconnect()
        return

    print(f"✅ 锁定目标歌曲: {target_track.artist} - {target_track.title}")
    
    # 2. 准备数据
    from core.cache_manager import load_cache
    cache = load_cache()
    
    # 准备目标 Track 数据
    target_analysis = cache.get(target_track.file_path)
    if not target_analysis:
        target_analysis = {
            'bpm': target_track.bpm,
            'key': target_track.key,
            'vocal_ratio': 0.5,
            'energy': target_track.rating * 20 if target_track.rating else 50,
            'file_path': target_track.file_path,
            'tags': []
        }
    elif 'analysis' in target_analysis:
        target_analysis = target_analysis['analysis']

    target_data = {
        'track_info': {'id': target_track.id, 'title': target_track.title, 'artist': target_track.artist, 'file_path': target_track.file_path},
        'analysis': target_analysis
    }

    # 准备候选池数据
    print(f"🧠 正在分析 {len(candidate_tracks)} 首候选曲目...")
    analyzed_candidates = []
    
    for t in candidate_tracks:
        if t.id == target_track.id: continue # 跳过自己
        
        # 简单去重 (ID)
        
        analysis = cache.get(t.file_path)
        if not analysis:
            analysis = {
                'bpm': t.bpm,
                'key': t.key,
                'vocal_ratio': 0.5,
                'energy': t.rating * 20 if t.rating else 50,
                'file_path': t.file_path,
                'tags': []
            }
        elif 'analysis' in analysis:
            analysis = analysis['analysis']
        
        analyzed_candidates.append({
            'track_info': {'id': t.id, 'title': t.title, 'artist': t.artist, 'file_path': t.file_path},
            'analysis': analysis
        })

    # 3. 计算分数 (1 * N)
    mi = MashupIntelligence()
    matches = []
    
    print(f"🔎 正在执行 {len(analyzed_candidates)} 次匹配计算...")
    
    for candidate in analyzed_candidates:
        score, details = mi.calculate_mashup_score(target_data, candidate, mode='mashup_discovery')
        
        if score >= threshold:
            matches.append({
                'score': score,
                'details': details,
                'track1': target_data, # 始终是目标歌曲
                'track2': candidate
            })
    
    # 排序
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # 4. 生成报告
    from datetime import datetime
    generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 清理文件名
    clean_name = "".join([c for c in query if c.isalpha() or c.isdigit() or c==' ' or c=='_']).strip()
    report_path = Path(f"D:/生成的set/search{clean_name}_MASHUP_RECOMMENDATIONS.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Mashup 专属报告: {target_track.title}\n\n")
        f.write(f"> **目标歌曲**: {target_track.artist} - {target_track.title} (BPM: {target_track.bpm}, Key: {target_track.key})\n")
        f.write(f"- **候选池**: {target_pl_obj.name} ({len(analyzed_candidates)} 首)\n")
        f.write(f"- **匹配数**: {len(matches)} (Threshold: {threshold})\n")
        f.write(f"- **时间**: {generation_time}\n\n")
        
        if not matches:
            f.write("⚠️ 未找到合适的高分匹配。\n")
        else:
            for idx, m in enumerate(matches[:top_n]):
                cand = m['track2']['track_info']
                cand_ana = m['track2']['analysis']
                
                f.write(f"### {idx+1}. [{m['score']:.1f}] vs {cand['title']}\n")
                f.write(f"**Candidate**: {cand['artist']} - {cand['title']}\n")
                f.write(f"- BPM: {cand_ana.get('bpm')} | Key: {cand_ana.get('key')} | Energy: {cand_ana.get('energy'):.1f}\n")
                
                f.write(f"\n**匹配详情**:\n")
                for k, v in m['details'].items():
                    if k == 'score': continue
                    f.write(f"- **{k.capitalize()}**: {v}\n")
                
                # 简要建议
                f.write(f"\n> 💡 **Mashup 提示**: {mi.generate_unified_guide(target_data, m['track2'], m['score'], m['details'])[0]}\n")
                f.write("\n---\n\n")

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
    parser.add_argument("--playlist", type=str, default="House", help="Rekordbox Playlist Name (Candidate Pool)")
    parser.add_argument("--threshold", type=float, default=70.0, help="Mashup score threshold")
    parser.add_argument("--query", type=str, help="Search for a specific track to find matches for")
    
    args = parser.parse_args()
    
    if args.query:
        asyncio.run(recommend_for_track(args.query, args.playlist, args.threshold))
    else:
        asyncio.run(recommend_mashups(args.playlist, args.threshold))
