#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Evolution Cloud Miner
- Bridges local library with cloud resources.
- Automatically finds missing Acapellas/Instrumentals for your tracks.
"""

import asyncio
import argparse
import sys
import os
from typing import List, Dict, Optional

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common_utils import load_clean_cache
from skill_cloud_discovery import CloudDiscovery
from skill_mashup_intelligence import MashupIntelligence
from evolution_config import PROFILES, DEFAULT_PROFILE

ACTIVE_PROFILE = PROFILES.get(DEFAULT_PROFILE)

class CloudMinerAgent:
    def __init__(self):
        self.miner = CloudDiscovery()
        self.intelligence = MashupIntelligence(ACTIVE_PROFILE.skill_settings)
        self.cache = load_clean_cache()

    def find_local_track(self, query: str) -> Optional[Dict]:
        """Find the source track in local cache to get target BPM/Key."""
        for _, data in self.cache.items():
            path = data.get('file_path', '')
            if query.lower() in os.path.basename(path).lower() or query.lower() in path.lower():
                return data
        return None

    async def run_mining(self, query: str, stem_type: str = "acapella", limit: int = 5, download: bool = False):
        print(f"🚀 [Cloud Miner] Targeting: '{query}' (Type: {stem_type})")
        
        # 1. Get Context (BPM/Key)
        source = self.find_local_track(query)
        if source:
            src_bpm = source.get('analysis', {}).get('bpm', 0)
            src_key = source.get('analysis', {}).get('key', 'Unknown')
            print(f"📍 Local Source Found: {os.path.basename(source.get('file_path'))}")
            print(f"   Target Specs: BPM {src_bpm:.1f}, Key {src_key}")
        else:
            print(f"⚠️  Note: '{query}' not found in local cache. Mining in 'Blind Search' mode.")
            src_bpm, src_key = 0, 'Unknown'

        # 2. Search Cloud
        candidates = self.miner.search_candidates(query, search_type=stem_type, limit=limit)
        
        print(f"\n🌐 Cloud Mining Results (Top {len(candidates)}):")
        print("=" * 60)
        
        for i, c in enumerate(candidates, 1):
            # Extract metadata from description
            meta = self.miner.extract_metadata_from_text(f"{c['title']} {c['description']}")
            c_bpm = meta.get('bpm', 0)
            c_key = meta.get('key', 'Unknown')
            
            match_status = "❓ Unknown"
            if src_bpm > 0 and c_bpm > 0:
                bpm_diff = abs(src_bpm - c_bpm)
                if bpm_diff < 5: match_status = "✅ BPM Match"
                elif bpm_diff < 10: match_status = "⚠️ BPM Shift Required"
                else: match_status = "❌ BPM Mismatch"
            
            print(f"{i}. {c['title']}")
            print(f"   - URL: {c['url']}")
            print(f"   - Specs: BPM {c_bpm or '?'}, Key {c_key or '?'}")
            print(f"   - Match: {match_status}")
            
            if download and i == 1: # Just download the top one if requested for demo
                save_name = f"cloud_{stem_type}_{query.replace(' ', '_')}"
                path = self.miner.download_track(c['url'], save_name)
                if path:
                    print(f"   🎉 Downloaded to: {path}")
            
        print("=" * 60)
        print("Tip: Use '--download' to fetch the top candidate automatically.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evolution Cloud Miner Agent")
    parser.add_argument("query", help="Track name to search for")
    parser.add_argument("--type", choices=["acapella", "instrumental", "remix"], default="acapella", help="Stem type")
    parser.add_argument("--limit", type=int, default=5, help="Search limit")
    parser.add_argument("--download", action="store_true", help="Download the top candidate")
    
    args = parser.parse_args()
    
    agent = CloudMinerAgent()
    asyncio.run(agent.run_mining(args.query, stem_type=args.type, limit=args.limit, download=args.download))
