
import sys
import os
from pathlib import Path

# Add core dir
sys.path.append(str(Path("d:/anti")))

from skills.mashup_intelligence.scripts.core import MashupIntelligence

def verify_isolation():
    print("=== Testing System Isolation (Sorter vs Discovery) ===")
    mi = MashupIntelligence()
    
    # CASE: Mandarin Pop x Techno (The Anti-Machine Scenario)
    t_vocal = {
        'track_info': {'title': 'Mandarin Vocal', 'artist': 'Jay'},
        'analysis': {'tags': ['mandarin', 'pop'], 'genre': 'c-pop', 'vocal_ratio': 0.8, 'bpm': 120}
    }
    t_techno = {
        'track_info': {'title': 'Cold Techno', 'artist': 'Machine'},
        'analysis': {'tags': ['techno', 'minimal'], 'genre': 'techno', 'vocal_ratio': 0.1, 'bpm': 120}
    }
    
    s1 = 0
    s2 = 0
    
    # 1. Test Sorter Mode
    print("\n[Mode: set_sorting]")
    try:
        s1, d1 = mi.calculate_mashup_score(t_vocal, t_techno, mode='set_sorting')
        print(f"Score: {s1:.1f}")
        if "Anti-Machine" not in str(d1):
            print("✅ SUCCESS: Sorter ignored Anti-Machine barrier.")
        else:
            print(f"❌ FAILED: Sorter triggered Anti-Machine! Details: {d1}")
    except Exception as e:
        print(f"❌ ERROR in Sorter Mode: {e}")

    # 2. Test Discovery Mode
    print("\n[Mode: mashup_discovery]")
    try:
        s2, d2 = mi.calculate_mashup_score(t_vocal, t_techno, mode='mashup_discovery')
        print(f"Score: {s2:.1f}")
        if "Anti-Machine" in str(d2):
            print("✅ SUCCESS: Recommender applied Anti-Machine barrier.")
        else:
            print(f"❌ FAILED: Recommender missed Anti-Machine! Details: {d2}")
    except Exception as e:
        print(f"❌ ERROR in Discovery Mode: {e}")

    # Compare
    if s1 > s2:
         print(f"\n✅ VERIFIED: Sorter Score ({s1}) > Discovery Score ({s2})")
    else:
         print(f"\n❌ FAILED: Scores are not different (s1={s1}, s2={s2})")

if __name__ == "__main__":
    verify_isolation()
