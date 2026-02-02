
import asyncio
from skills.mashup_intelligence.scripts.core import MashupIntelligence, SonicMatcher

def test_ninja_dsp():
    print("🧪 Verifying Ninja x Foot Fungus DSP Pipeline...")
    
    # 1. Setup Mock Tracks with Real File Paths (where available)
    # We use the temp_audio.wav we verified earlier as a stand-in for "real audio" 
    # to trigger the DSP engine, even if the content isn't actually Ninja.
    # The goal is to prove the PIPELINE calls YAMNet.
    
    real_audio_path = "d:/anti/downloads/newjeans_analysis/temp_audio.wav"
    
    # Track 1: Ninja (We simulate it has a file so it triggers DSP)
    # Note: If the file doesn't match 'Zither', we won't get the bonus, 
    # but we will see the DSP tags in the logs/output.
    t1 = {
        'track_info': {
            'title': 'Ninja',
            'artist': '7981 Kal',
            'file_path': real_audio_path 
        },
        'analysis': {'bpm': 105.0, 'key': '8A'}
    }
    
    # Track 2: Foot Fungus (Heuristic Fallback or Real)
    t2 = {
        'track_info': {
            'title': 'Foot Fungus',
            'artist': 'Ski Mask',
            'file_path': 'd:/anti/mock_foot_fungus.mp3' # Non-existent, will fallback to heuristic
        },
        'analysis': {'bpm': 105.0, 'key': '8A'}
    }

    # 2. Run Matcher
    mi = MashupIntelligence()
    
    # We want to see if 'analyze_file' is called on t1
    print(f"🔎 Analyzing {t1['track_info']['title']} (Real Audio) x {t2['track_info']['title']} (Mock)...")
    
    score, details = mi.calculate_mashup_score(t1, t2)
    
    print(f"\n🏆 Final Score: {score}")
    print("📝 Details:")
    for k, v in details.items():
        print(f"  - {k}: {v}")

    # Check for DSP evidence in "sonic_dna" or logs
    # Note: Since temp_audio.wav is Techno, we won't get the 'Oriental' bonus 
    # unless we fake the return of the DSP engine for this test.
    # But let's see what it actually returns first.
    
    # Direct probe of the matcher to see tags
    matcher = SonicMatcher()
    print("\n🔬 Direct DSP Tag Probe on 'Ninja' File:")
    tags = matcher.analyze_file(real_audio_path)
    print(f"  -> Generated Tags: {tags}")

if __name__ == "__main__":
    test_ninja_dsp()
