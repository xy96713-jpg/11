
import sys
import os
import json
from pathlib import Path

# Setup paths
BASE_DIR = Path("d:/anti")
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

from skills.mashup_intelligence.scripts.core import MashupIntelligence
from core.common_utils import load_cache, normalize_path

# Fix Windows encoding for Chinese/Korean characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def find_ninja_matches():
    mi = MashupIntelligence()
    
    # 1. Load Ninja DNA
    cache = load_cache()
    ninja_path = normalize_path('D:/song/周杰伦/2001-范特西/周杰伦 - 忍者.flac')
    ninja_entry = cache.get(ninja_path)
    
    if not ninja_entry:
        print("Error: Ninja (忍者) not found in cache.")
        return

    ninja_track = {
        'track_info': {'title': '忍者', 'artist': '周杰伦'},
        'analysis': ninja_entry['analysis']
    }
    
    # 2. Scan library for candidates
    print(f"Scanning library for '忍者' (BPM: {ninja_track['analysis']['bpm']}, Key: {ninja_track['analysis']['key']}) Mashups...")
    
    results = []
    
    for path, entry in cache.items():
        if path == ninja_path:
            continue
            
        candidate_track = {
            'track_info': {'title': Path(path).stem, 'artist': entry.get('artist', 'Unknown')},
            'analysis': entry['analysis']
        }
        
        # Use V7.1 Discovery Mode
        score, details = mi.calculate_mashup_score(ninja_track, candidate_track, mode='mashup_discovery')
        
        # Filtering for relevance
        if score > 70:
            results.append({
                'score': score,
                'title': candidate_track['track_info']['title'],
                'artist': candidate_track['track_info']['artist'],
                'details': details
            })
            
    # Sort and Print Top 10
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "="*80)
    print(f" TOP MASHUP PICKS FOR: 忍者 (Jay Chou) - V7.1 Contrast Engine")
    print("="*80)
    
    for i, res in enumerate(results[:10]):
        print(f"{i+1}. [{res['score']:.1f} pts] {res['title']} - {res['artist']}")
        # Format details
        affinity = res['details'].get('cultural_affinity', 'Standard')
        mashup_p = res['details'].get('mashup_pattern', 'N/A')
        key_h = res['details'].get('key', 'N/A')
        print(f"   Vibe: {affinity} | Pattern: {mashup_p} | Key: {key_h}")
        if 'bass_clash' in res['details']:
            print(f"   ⚠️ Warning: {res['details']['bass_clash']}")
        print("-" * 40)

if __name__ == "__main__":
    find_ninja_matches()
