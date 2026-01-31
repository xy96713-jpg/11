#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJ Evolution System (V6.4) - Pro Experience Wrapper
Integrates Professional Sorting, Global Optimization, Mixing Radar, and XML Export.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Import Evolution Components
from enhanced_harmonic_set_sorter import create_enhanced_harmonic_sets, ACTIVE_PROFILE
from rekordbox_xml_generator import generate_rekordbox_xml, enrich_track_with_enhanced_features
import evolution_config

class SimpleLogger:
    def log(self, message, console=True):
        if console:
            print(f"  {message}")

async def run_pro_experience(playlist_name, profile_key, export_xml=True):
    print("=" * 60)
    print(f" [OK] DJ Evolution System V6.4: PRO EXPERIENCE ")
    print("=" * 60)
    
    # 1. Switch Profile
    if profile_key in evolution_config.PROFILES:
        import enhanced_harmonic_set_sorter
        enhanced_harmonic_set_sorter.ACTIVE_PROFILE = evolution_config.PROFILES[profile_key]
        profile = enhanced_harmonic_set_sorter.ACTIVE_PROFILE
        print(f"[*] 激活策略: {profile.name}")
        print(f"[*] 策略描述: {profile.description}")
        # 显示规则细节
        s = profile.skill_settings
        print(f"    - 人声预警: 提前 {s['vocal_warning_bars']} 小节")
        print(f"    - 雷达阈值: Risk<{s['radar_risk_threshold']}, Conflict<{s['radar_conflict_threshold']}")
    else:
        print(f"[!] 警告: 未找到策略 {profile_key}，使用默认值。")
        profile = ACTIVE_PROFILE

    # 2. Generate Set (includes Phase 1, 2, 3)
    logger = SimpleLogger()
    print("\n[*] 正在启动进化引擎 (排序 -> 智力技能 -> 全局退火)...")
    
    # create_enhanced_harmonic_sets returns the optimized sets
    # We call it with progress_logger
    from enhanced_harmonic_set_sorter import create_enhanced_harmonic_sets
    
    # Note: create_enhanced_harmonic_sets technically exports M3U and Reports internally, 
    # but we want the track objects for XML.
    # We'll need a way to get the results.
    # Actually, create_enhanced_harmonic_sets currently doesn't return the sets easily, 
    # but we can modify it or mock the call.
    
    # For now, let's run the generator and then read the tracks.
    # To keep it simple, I'll inform create_enhanced_harmonic_sets is the main entry.
    
    # If the user wants XML, we need the track objects.
    # Let's add a return value to create_enhanced_harmonic_sets or create a light version.
    
    print("\n[第一阶段] 基础排序与全局优化...")
    sets = await create_enhanced_harmonic_sets(
        playlist_name=playlist_name,
        songs_per_set=40,
        progress_logger=logger
    )
    
    if not sets:
        print("[!] 错误: 未生成任何 Set。")
        return

    print("\n[第二阶段] 智能 Hot Cues 与 XML 深度集成...")
    if export_xml:
        target_set = sets[0] # 默认处理第一个 Set
        print(f"[*] 正在为 Set 1 ({len(target_set)} 首歌曲) 生成增强型 Hot Cues...")
        
        enriched_tracks = []
        for i, track in enumerate(target_set):
            print(f"    [{i+1}/{len(target_set)}] 分析: {track.get('title')[:30]}")
            # 注入增强数据 (Hot Cues, Beatgrid, Advice)
            enriched = enrich_track_with_enhanced_features(track)
            enriched_tracks.append(enriched)
            
        xml_name = f"Evolution_{profile_key}_{playlist_name}"
        xml_path = generate_rekordbox_xml(enriched_tracks, xml_name)
        
        print("\n" + "=" * 60)
        print(" [SUCCESS] 进化版体验生成成功！")
        print("=" * 60)
        print(f" 1. M3U 顺序已更新 (见 D:\\生成的set)")
        print(f" 2. 混音雷达报告已生成 (见 D:\\生成的set)")
        print(f" 3. 灵魂组件：XML 数据库已生成 -> {xml_path}")
        print("\n 操作指南：")
        print(" - 请在 Rekordbox 的 'rekordbox xml' 栏目中导入该文件。")
        print(" - 体验：波形中已包含 红色人声预警 (E/F/G) 与 自动混音标记。")
        print("=" * 60)
    else:
        print("[*] XML 导出已禁用，仅生成 M3U 与报告。")

async def main():
    parser = argparse.ArgumentParser(description="DJ Evolution Pro Experience")
    parser.add_argument("playlist", help="Playlist name in Rekordbox")
    parser.add_argument("--profile", default="BALANCED_ALPHA", choices=list(evolution_config.PROFILES.keys()), help="Scoring profile")
    parser.add_argument("--no-xml", action="store_true", help="Disable XML generation")
    
    args = parser.parse_args()
    
    await run_pro_experience(args.playlist, args.profile, not args.no_xml)

if __name__ == "__main__":
    asyncio.run(main())
