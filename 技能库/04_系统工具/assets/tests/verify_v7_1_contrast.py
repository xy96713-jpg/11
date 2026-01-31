
import sys
import os
from pathlib import Path

# Add core dir
sys.path.append(str(Path("d:/anti")))

from skills.mashup_intelligence.scripts.core import MashupIntelligence

def verify_v7_1():
    print("=== Testing V7.1 Contrast Engine (Golden Cluster & Anti-Machine) ===")
    mi = MashupIntelligence()
    
    # Mock Tracks
    # 1. Mandarin Pop (Vocal heavy)
    t_mandarin = {
        'track_info': {'title': 'Mandarin Song', 'artist': 'Jay Chou'},
        'analysis': {'tags': ['mandarin', 'pop'], 'genre': 'c-pop', 'vocal_ratio': 0.8, 'bpm': 120}
    }
    
    # 2. K-Pop (Vocal heavy)
    t_kpop = {
        'track_info': {'title': 'K-Pop Song', 'artist': 'NewJeans'},
        'analysis': {'tags': ['k-pop', 'dance'], 'genre': 'k-pop', 'vocal_ratio': 0.7, 'bpm': 120}
    }
    
    # 3. Western Hip-Hop
    t_hiphop = {
        'track_info': {'title': 'rap god', 'artist': 'Eminem'},
        'analysis': {'tags': ['hip hop', 'rap'], 'genre': 'hip hop', 'vocal_ratio': 0.9, 'bpm': 120}
    }
    
    # 4. Pure Minimal Techno (No vocal)
    t_techno = {
        'track_info': {'title': 'Dark Room', 'artist': 'Unknown'},
        'analysis': {'tags': ['minimal', 'techno'], 'genre': 'techno', 'vocal_ratio': 0.1, 'bpm': 120}
    }
    
    # 5. House (Control)
    t_house1 = {
        'track_info': {'title': 'House 1', 'artist': 'A'},
        'analysis': {'tags': ['house'], 'genre': 'house', 'vocal_ratio': 0.4, 'bpm': 120}
    }
    t_house2 = {
        'track_info': {'title': 'House 2', 'artist': 'B'},
        'analysis': {'tags': ['house'], 'genre': 'house', 'vocal_ratio': 0.4, 'bpm': 120}
    }

    # Case 1: Mandarin x K-Pop (Golden Cluster)
    print("\n[Case 1] Mandarin x K-Pop")
    s, d = mi.calculate_mashup_score(t_mandarin, t_kpop)
    print(f"Score: {s:.1f}")
    if "Golden Cluster" in str(d):
        print("✅ SUCCESS: Detected 'Golden Cluster'")
    else:
        print(f"❌ FAILED: Details: {d}")

    # Case 2: Mandarin x Hip-Hop (Golden Cluster)
    print("\n[Case 2] Mandarin x Hip-Hop")
    s, d = mi.calculate_mashup_score(t_mandarin, t_hiphop)
    print(f"Score: {s:.1f}")
    if "Golden Cluster" in str(d):
        print("✅ SUCCESS: Detected 'Golden Cluster'")
    else:
        print(f"❌ FAILED: Details: {d}")

    # Case 3: Mandarin x Techno (Anti-Machine)
    print("\n[Case 3] Mandarin x Techno")
    s, d = mi.calculate_mashup_score(t_mandarin, t_techno)
    print(f"Score: {s:.1f}")
    if "Anti-Machine" in str(d):
        print("✅ SUCCESS: Triggered 'Anti-Machine' Barrier")
    else:
        print(f"❌ FAILED: Details: {d}")
        
    # Case 4: House x House (Control)
    print("\n[Case 4] House x House (Control)")
    s, d = mi.calculate_mashup_score(t_house1, t_house2)
    print(f"Score: {s:.1f}")
    if "Golden Cluster" not in str(d) and "Anti-Machine" not in str(d):
        print("✅ SUCCESS: No special bonus/penalty")
    else:
        print(f"❌ FAILED: Unexpected details: {d}")

if __name__ == "__main__":
    verify_v7_1()
