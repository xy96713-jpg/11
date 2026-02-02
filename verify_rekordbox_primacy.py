
import asyncio
from typing import Dict, List
import sys
import os

# Add paths
sys.path.insert(0, "d:/anti")
from skills.mashup_intelligence.scripts.core import MashupIntelligence, SonicMatcher

def test_rekordbox_primacy():
    print("🛡️ V31.0 Rekordbox Primacy Verification")
    print("Ensuring USER BPM is law, and DSP is only an advisor.\n")
    
    # 1. Setup Tracks with STRICT User BPMs
    # We pretend these are from Rekordbox
    
    # Ninja: User says 71. DSP will likely estimate ~140 or ~70 depending on librosa logic.
    # We want to ensure 71 is used for scoring.
    t1 = {
        'track_info': {
            'title': 'Ninja',
            'artist': '7981 Kal',
            'file_path': "d:/anti/downloads/newjeans_analysis/temp_audio.wav" # Using temp audio to trigger DSP
        },
        'analysis': {'bpm': 71.0, 'key': '8A'}, # REKORDBOX TRUTH
        'vibe': {'tags': []} 
    }
    
    # Foot Fungus: User says 77.
    t2 = {
        'track_info': {
            'title': 'Foot Fungus',
            'artist': 'Ski Mask',
            'file_path': "d:/anti/downloads/newjeans_analysis/temp_audio.wav" 
        },
        'analysis': {'bpm': 77.0, 'key': '8A'}, # REKORDBOX TRUTH
        'vibe': {'tags': []}
    }
    
    # 2. Run Matcher
    mi = MashupIntelligence()
    
    print(f"🔎 Analyzing {t1['track_info']['title']} ({t1['analysis']['bpm']} BPM) x {t2['track_info']['title']} ({t2['analysis']['bpm']} BPM)...")
    
    score, details = mi.calculate_mashup_score(t1, t2)
    
    print(f"\n🏆 Final Score: {score}")
    print("📝 Details:")
    for k, v in details.items():
        print(f"  - {k}: {v}")
        
    # 3. Verification Logic
    # Check if BPM Score reflects the 71 vs 77 gap (approx 8% diff)
    # 71 / 77 = 0.92 -> 8% diff.
    # Should fall into "Professional" or "Creative Risk" tier depending on tolerance.
    # Definitely NOT "Golden" (0-4%).
    
    # Also verify that DSP didn't overwrite the input dict
    if t1['analysis']['bpm'] != 71.0:
        print("\n❌ CRITICAL FAIL: DSP overwrote User BPM!")
    else:
        print("\n✅ PASS: User BPM intact (71.0).")
        
    # Verify DSP tags were actually fetched (we hooked them up in core.py)
    # Note: calculate_mashup_score doesn't return the tags explicitly in details usually,
    # but 'sonic_dna' detail would show if a bonus was found.
    # Since our temp_audio.wav isn't actually Ninja, we might not get the 'Oriental' tag.
    # But let's check the cortex cache or logs to see if it ran.
    
    from core.audio_cortex import cortex
    print("\n🔬 Checking AudioCortex Cache:")
    fname = "temp_audio.wav"
    if fname in cortex.cache:
         print(f"  - Entry found for {fname}")
         print(f"  - Keys: {cortex.cache[fname].keys()}")
         if 'dsp_estimated_bpm' in cortex.cache[fname]:
             print(f"  - DSP Est. BPM: {cortex.cache[fname]['dsp_estimated_bpm']}")
    else:
         print("  - No cache entry found (Did DSP run?)")

if __name__ == "__main__":
    test_rekordbox_primacy()
