#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill: Cloud Discovery
- Searches for Acapellas/Instrumentals on the cloud (YouTube, SoundCloud, etc.)
- Uses yt-dlp to bypass scraping restrictions.
- Extracts basic metadata (BPM/Key) if present in descriptions.
"""

import os
import subprocess
import json
import re
import sys
from typing import List, Dict, Optional

class CloudDiscovery:
    def __init__(self, download_dir: str = "downloads/cloud_stems"):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
    def generate_smart_query(self, track_info: Dict, search_type: str = "acapella") -> List[str]:
        """
        Generate a list of search queries from specific to broad.
        """
        title = track_info.get('track_info', {}).get('title')
        if not title:
            file_path = track_info.get('file_path', 'Unknown')
            title = os.path.basename(file_path).replace('.mp3', '').replace('.wav', '')
            
        artist = track_info.get('track_info', {}).get('artist', '')
        analysis = track_info.get('analysis', {})
        bpm = analysis.get('bpm', 100)
        camelot_key = analysis.get('key', '')
        
        queries = []
        
        # Tier 1: High-Quality Specific (Studio Acapella)
        queries.append(f"{artist} {title} Studio {search_type}".strip())
        
        # Tier 2: Creative & Vibe-Aware
        energy = analysis.get('energy', 0.5)
        vibe = "Funky/Street/High Energy" if energy > 0.6 else "Smooth/R&B"
        queries.append(f"{artist} {title} {vibe} {search_type} {camelot_key}".strip())
        
        # Tier 3: Industry Mashup/Edit Search
        queries.append(f"{title} {bpm}bpm DJ Mashup Pack".strip())
        
        return queries

    def search_candidates(self, track_info: Dict, search_type: str = "acapella", limit: int = 5, flavor: str = None) -> List[Dict]:
        """
        Multi-tiered cloud search.
        """
        if isinstance(track_info, str):
            tier_queries = [f"{track_info} {flavor or ''} {search_type}".strip()]
        else:
            tier_queries = self.generate_smart_query(track_info, search_type)
            if flavor:
                tier_queries = [f"{q} {flavor}" for q in tier_queries]
                
        all_candidates = []
        negatives = ["健身操", "workout", "karaoke", "tutorial", "lesson", "reaction", "review"]
        
        for query in tier_queries:
            print(f"🌐 Searching Cloud (Tier {tier_queries.index(query)+1}): '{query}'...")
            
            cmd = [
                sys.executable, "-m", "yt_dlp",
                f"ytsearch{limit}:{query}",
                "--dump-json",
                "--flat-playlist",
                "--quiet"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                for line in result.stdout.splitlines():
                    if not line.strip(): continue
                    info = json.loads(line)
                    
                    title = info.get('title') or ""
                    desc = info.get('description') or ""
                    title_lower = title.lower()
                    desc_lower = desc.lower()
                    
                    if any(neg in title_lower or neg in desc_lower for neg in negatives):
                        continue
                        
                    candidate = {
                        'title': info.get('title'),
                        'url': info.get('url') or f"https://www.youtube.com/watch?v={info.get('id')}",
                        'id': info.get('id'),
                        'duration': info.get('duration'),
                        'uploader': info.get('uploader'),
                        'description': info.get('description', ''),
                        'source': 'youtube'
                    }
                    
                    # Avoid duplicated URLs
                    if not any(c['url'] == candidate['url'] for c in all_candidates):
                        all_candidates.append(candidate)
                        
                if len(all_candidates) >= limit:
                    break # Sufficient results found
                    
            except Exception as e:
                print(f"   ⚠️  Tier failed: {e}")
                
        return all_candidates[:limit]

    def extract_metadata_from_text(self, text: str) -> Dict:
        """
        Try to find BPM and Key patterns in titles or descriptions.
        """
        meta = {}
        # BPM Pattern: "128bpm", "BPM: 120"
        bpm_match = re.search(r'(\d{2,3})\s*(?:bpm|BPM)', text, re.IGNORECASE)
        if bpm_match:
            meta['bpm'] = float(bpm_match.group(1))
            
        # Key Pattern: "8A", "12B", "Am", "C# Minor"
        camelot_match = re.search(r'(\d{1,2}[AB])', text, re.IGNORECASE)
        if camelot_match:
            meta['key'] = camelot_match.group(1).upper()
            
        return meta

    def download_track(self, url: str, output_name: str) -> Optional[str]:
        """
        Download the specific track and return the final file path.
        """
        output_path = os.path.join(self.download_dir, f"{output_name}.%(ext)s")
        print(f"⬇️  Downloading from cloud: {url}")
        
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-x", # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0", # Best quality
            "-o", output_path,
            url
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            # Find the actual file (yt-dlp might change extension)
            for f in os.listdir(self.download_dir):
                if f.startswith(output_name):
                    return os.path.join(self.download_dir, f)
            return None
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

if __name__ == "__main__":
    # Smoke test
    miner = CloudDiscovery()
    results = miner.search_candidates("One Dance", limit=2)
    for r in results:
        print(f"Found: {r['title']} ({r['url']})")
        meta = miner.extract_metadata_from_text(f"{r['title']} {r['description']}")
        print(f"Meta: {meta}")
