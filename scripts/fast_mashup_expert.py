
import sys
import os
import io
import json
from pathlib import Path
from datetime import datetime

# Setup paths
BASE_DIR = Path("d:/anti")
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

# Fix Windows encoding for Chinese/Korean characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from skills.mashup_intelligence.scripts.core import MashupIntelligence
from core.common_utils import load_cache, normalize_path

def fast_find(query_name, threshold=70):
    mi = MashupIntelligence()
    cache = load_cache()
    
    # 1. Find Target Song
    ref_track = None
    ref_path = None
    
    print(f"🚀 [Fast Path] Searching for '{query_name}' in cache...")
    for path, entry in cache.items():
        if query_name.lower() in path.lower() or query_name.lower() in Path(path).stem.lower():
            ref_path = path
            ref_track = {
                'track_info': {'title': Path(path).stem, 'artist': entry.get('artist', 'Unknown')},
                'analysis': entry['analysis']
            }
            break
            
    if not ref_track:
        print(f"❌ Error: Song '{query_name}' not found in analysis cache.")
        return

    # Use global arousal mean for better context
    vibe = ref_track['analysis'].get('vibe_analysis', {})
    arousal = ref_track['analysis'].get('arousal_window_mean', vibe.get('arousal', 0.5))
    mood = ref_track['analysis'].get('vocal_mood', 'N/A')
    
    print(f"✅ Found: {ref_track['track_info']['title']}")
    print(f"   BPM: {ref_track['analysis']['bpm']:.2f} | Energy (Arousal): {arousal:.2f} | Mood: {mood}")
    
    # 2. Run Scan
    results = []
    total = len(cache)
    print(f"⚡ Scanning {total} tracks using V7.2 Dyna-Vibe Logic...")
    
    for path, entry in cache.items():
        if path == ref_path:
            continue
            
        candidate = {
            'track_info': {'title': Path(path).stem, 'artist': entry.get('artist', 'Unknown')},
            'analysis': entry['analysis']
        }
        
        score, details = mi.calculate_mashup_score(ref_track, candidate, mode='mashup_discovery')
        
        if score >= threshold:
            results.append({
                'score': score,
                'title': candidate['track_info']['title'],
                'artist': candidate['track_info']['artist'],
                'details': details
            })

    # 3. Output Report
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "="*80)
    print(f" V7.2 EXPERT MASHUP PICKS: {ref_track['track_info']['title']}")
    print(f" Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    for i, res in enumerate(results[:10]):
        print(f"{i+1}. [{res['score']:.1f} pts] {res['title']} - {res['artist']}")
        
        # Affinity & Synergy
        affinity = res['details'].get('cultural_affinity', 'Standard')
        mashup_p = res['details'].get('mashup_pattern', 'N/A')
        print(f"   Vibe Strategy: {affinity}")
        
        # Highlight Logic
        if "🔥" in affinity:
            print(f"   ✅ [V7.2 SYNERGY] 能量/情绪完美锁位")
            
        # BPM Tier Feedback
        bpm_tier = res['details'].get('bpm_tier', 'Standard')
        if bpm_tier == "Golden":
            print(f"   💎 [BPM GOLDEN] 高保真匹配 (±5%)")
        elif bpm_tier == "Elastic":
            print(f"   🎢 [BPM ELASTIC] 弹性跨度 (±10%) -> 🎚️ 请确认 Master Tempo 已开启")
            
        if "💔" in affinity:
            print(f"   ⚠️ [Vibe Clash] 能量严重脱节")
        if "📉" in affinity:
            print(f"   🚫 [Mismatch] 强弱失调，听感可能突兀")

        # Technical
        print(f"   Pattern: {mashup_p} | Key: {res['details'].get('key', 'N/A')}")
        if 'bass_clash' in res['details']:
            print(f"   ☢️ Bass: {res['details']['bass_clash']}")
        print("-" * 50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fast_find(sys.argv[1])
    else:
        print("Usage: python fast_mashup_expert.py <song_name>")
