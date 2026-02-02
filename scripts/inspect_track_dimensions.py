import json
import sys
import os
from pathlib import Path
import argparse

# Configuration
CACHE_PATH = r"d:\anti\scripts\song_analysis_cache.json"

def load_cache():
    if not os.path.exists(CACHE_PATH):
        print(f"❌ Cache not found at {CACHE_PATH}")
        return {}
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def inspect_track(query: str):
    cache = load_cache()
    matches = []
    
    # Simple search
    for key, data in cache.items():
        file_path = data.get('file_path', '')
        if query.lower() in file_path.lower() or query.lower() in key.lower():
            matches.append((key, data))
    
    if not matches:
        print(f"❓ No match found for '{query}'")
        return

    # Pick the first match
    key, data = matches[0]
    analysis = data.get('analysis', {})
    
    print("=" * 60)
    print(f"📊 DIMENSION BRIEF: {Path(data.get('file_path')).name}")
    print("=" * 60)
    print(f"🔑 Cache Key: {key}")
    print(f"📍 File Path: {data.get('file_path')}")
    print("-" * 60)
    
    # Core Dimensions
    print(f"🎼 BPM: {analysis.get('bpm', 'N/A')} ({analysis.get('bpm_status', 'N/A')})")
    print(f"🎹 Key: {analysis.get('key', 'N/A')} (Confidence: {analysis.get('key_confidence', 0):.2f})")
    print(f"⚡ Energy: {analysis.get('energy', 'N/A')}/100")
    print(f"🎤 Vocal Ratio: {analysis.get('vocal_ratio', 0):.2f}")
    
    # Sonic DNA (The 101st Dimension)
    print(f"🧬 Sonic DNA: {analysis.get('sonic_dna', [])}")
    
    # Advanced Dimensions (The 100+)
    print("-" * 60)
    print("🧠 Advanced Dimensions (Selection):")
    skip_keys = ['bpm', 'key', 'energy', 'vocal_ratio', 'sonic_dna', 'structure', 'vocals', 'drums', 'energy_profile', 'vocal_sections', 'key_modulations']
    
    count = 0
    for k, v in analysis.items():
        if k not in skip_keys and not isinstance(v, (dict, list)):
            print(f"  - {k:25}: {v}")
            count += 1
            if count > 15: # Limit for readability
                print("  - ... and more")
                break
                
    # Profiles
    ep = analysis.get('energy_profile', {})
    if ep:
        print(f"🎸 Groove Density: {ep.get('groove_density', 'N/A')}")
        print(f"🥁 Percussive Ratio: {ep.get('percussive_ratio', 'N/A'):.2f}")

    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Track Dimensions")
    parser.add_argument("query", help="Part of file path or cache key")
    args = parser.parse_args()
    inspect_track(args.query)
