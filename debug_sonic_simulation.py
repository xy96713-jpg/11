
import sys
import asyncio
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/skills/mashup_intelligence/scripts")

from core import MashupIntelligence, SonicMatcher

def test_sonic_simulation():
    print("--- Simulating V22.0 Sonic DNA ---")
    
    mi = MashupIntelligence()
    
    # Simulate Ninja
    t1 = {
        'title': 'Jay Chou - Ninja',
        'track_info': {'title': 'Jay Chou - Ninja'},
        'analysis': {
            'bpm': 105.26, 
            'key': '9A',
            'energy': 0.8,
            'vocal_ratio': 0.8
        }
    }
    
    # Simulate Foot Fungus
    t2 = {
        'title': 'Foot Fungus (Matthewville Edit)',
        'track_info': {'title': 'Foot Fungus (Matthewville Edit)'},
        'analysis': {
            'bpm': 100.0, 
            'key': '1A', # Key Clash!
            'energy': 0.8,
            'vocal_ratio': 0.5
        }
    }
    
    score, details = mi.calculate_mashup_score(t1, t2)
    
    print(f"Match: {t1['title']} x {t2['title']}")
    print(f"Base Key: {t1['analysis']['key']} vs {t2['analysis']['key']}")
    print(f"FINAL SCORE: {score}")
    print(f"Details:")
    for k, v in details.items():
        print(f"  {k}: {v}")

    if "sonic_dna" in details and "+30.0" in details['sonic_dna']:
        print("\nSUCCESS: Sonic Bonus Applied!")
    else:
        print("\nFAILURE: Bonus logic missing.")

if __name__ == "__main__":
    test_sonic_simulation()
