#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Evolution Mashup Agent
- Standalone CLI for finding the perfect "Stems Layering" partner.
- Uses SkillMashupIntelligence for professional 11-dimension scoring.
"""

import asyncio
import argparse
import sys
import os
from typing import List, Dict, Optional

# 添加导入路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "core"))
sys.path.insert(0, os.path.join(BASE_DIR, "skills"))
sys.path.insert(0, os.path.join(BASE_DIR, "config"))

from common_utils import load_clean_cache
from skill_mashup_intelligence import MashupIntelligence
from evolution_config import PROFILES, DEFAULT_PROFILE

ACTIVE_PROFILE = PROFILES.get(DEFAULT_PROFILE)

async def find_mashup_partners(query: str = None, playlist_name: str = None, top_k: int = 10, threshold: float = None, enable_cloud: bool = False, vibe: str = None):
    print(f"🔍 [Evolution Mashup Agent] Starting discovery (Vibe: {vibe or 'Neutral'})...")
    
    # ... (skipping unchanged code)
    cache = load_clean_cache()
    if not cache:
        print("❌ Error: Cache is empty. Please run analysis first.")
        return

    skill = MashupIntelligence(ACTIVE_PROFILE.skill_settings)
    if threshold is not None:
        skill.mashup_threshold = threshold
        print(f"⚙️  Using custom threshold: {threshold}")
    
    # 2. Identify Source Track(s)
    source_tracks = []
    if query:
        print(f"🔎 Searching for source track: '{query}'")
        for _, data in cache.items():
            path = data.get('file_path', '')
            title = os.path.basename(path).lower()
            if query.lower() in title or query.lower() in path.lower():
                source_tracks.append(data)
        if not source_tracks:
            if enable_cloud:
                print(f"⚠️  No tracks matching '{query}' found in local cache. Proceeding with BLIND CLOUD SEARCH.")
                source_tracks = [None] # Use a placeholder
            else:
                print(f"❌ No tracks matching '{query}' found in cache.")
                return
        else:
            print(f"✅ Found {len(source_tracks)} local source candidates.")
    elif playlist_name:
        print(f"📂 Scanning playlist: '{playlist_name}' (Not implemented - falling back to all cache)")
        source_tracks = list(cache.values())

    # 3. Discovery Loop (Local)
    all_tracks = list(cache.values())
    matches = []
    
    for src in source_tracks:
        if not src: continue 
        src_path = src.get('file_path', 'Unknown')
        src_title = os.path.basename(src_path)
        print(f"   🕺 Finding local matches for: {src_title}")
        
        for tgt in all_tracks:
            if src.get('file_path') == tgt.get('file_path'): continue
            
            # [最强大脑修正] 强制跨歌手过滤 (除非用户指定)
            src_artist = str(src.get('file_path','')).lower()
            tgt_artist = str(tgt.get('file_path','')).lower()
            # 简单模糊匹配歌手名 (可以通过路径中的文件夹名推断)
            if ("jaychou" in tgt_artist or "周杰伦" in tgt_artist) and ("jaychou" in src_artist or "周杰伦" in src_artist):
                continue
            
            score, details = skill.calculate_mashup_score(src, tgt)
            if score >= skill.mashup_threshold:
                matches.append({'src': src, 'tgt': tgt, 'score': score, 'details': details, 'type': 'local'})

    # 4. Discovery Loop (Cloud)
    if enable_cloud and query:
        try:
            from skill_cloud_discovery import CloudDiscovery
            miner = CloudDiscovery()
            
            # If no vibe provided, try to extract from source track info
            search_vibe = vibe
            if not search_vibe and source_tracks:
                # Try to get genre or style from metadata
                search_vibe = source_tracks[0].get('track_info', {}).get('genre', '')
            
            # Use the full dimension data for smart search
            print(f"   🌐 [Cloud] Dimension-Aware Search for candidates matching '{query}'...")
            search_anchor = source_tracks[0] if source_tracks[0] else query
            cloud_results = miner.search_candidates(search_anchor, search_type="acapella", limit=5, flavor=vibe)
            for c in cloud_results:
                matches.append({
                    'src': source_tracks[0],
                    'tgt_title': c['title'],
                    'url': c['url'],
                    'score': 70.0,
                    'type': 'cloud'
                })
        except Exception as e:
            print(f"   ⚠️  Cloud mining skipped: {e}")

    # 5. Sort and Display
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n🏆 Top {top_k} Mashup Recommendations:")
    print("=" * 60)
    
    count = 0
    for m in matches:
        if count >= top_k: break
        count += 1
        
        if m['type'] == 'local':
            src_t = m['src'].get('track_info',{}).get('title') or os.path.basename(m['src'].get('file_path',''))
            tgt_t = m['tgt'].get('track_info',{}).get('title') or os.path.basename(m['tgt'].get('file_path',''))
            print(f"{count}. [LOCAL] {src_t} (+/-) {tgt_t} [Score: {m['score']:.1f}]")
            print(f"   - Match: {m['details'].get('key', 'Unknown')}")
        else:
            src_name = query # Reference the original query for blind searches
            if m['src']:
                src_name = m['src'].get('track_info',{}).get('title') or os.path.basename(m['src'].get('file_path',''))
            print(f"{count}. [CLOUD] {src_name} (+/-) {m['tgt_title']} [Score: {m['score']:.1f}]")
            print(f"   - Link: {m['url']}")
            print(f"   - Action: Use 'evolution_cloud_miner_agent.py' to download and verify.")
        print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evolution Mashup Agent")
    parser.add_argument("--query", help="Track name or path to find partners for")
    parser.add_argument("--playlist", help="Playlist name to scan")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--threshold", type=float, help="Override threshold")
    parser.add_argument("--cloud", action="store_true", help="Enable cloud discovery")
    parser.add_argument("--vibe", help="Style/Flavor keyword (e.g. Afro, Funky)")
    args = parser.parse_args()

    asyncio.run(find_mashup_partners(
        query=args.query, 
        playlist_name=args.playlist, 
        top_k=args.limit,
        threshold=args.threshold,
        enable_cloud=args.cloud,
        vibe=args.vibe
    ))
