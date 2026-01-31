import sys
import os
from pathlib import Path

# Add core dir to sys.path
sys.path.append(str(Path("d:/anti")))

try:
    from enhanced_harmonic_set_sorter import _calculate_candidate_score
except ImportError:
    print("Failed to import _calculate_candidate_score. Checking file path...")
    import enhanced_harmonic_set_sorter
    _calculate_candidate_score = enhanced_harmonic_set_sorter._calculate_candidate_score

def test_rhythmic_scoring():
    print("=== V6.2 Rhythmic Scoring Verification ===")
    
    # Mock tracks
    current_track = {
        'title': '4/4 Track',
        'bpm': 124.0,
        'key': '1A',
        'time_signature': '4/4',
        'swing_dna': 0.05  # Straight
    }
    
    # Test 1: Matching Meter (Good)
    good_track = {
        'title': 'Matching 4/4',
        'bpm': 124.0,
        'key': '1A',
        'time_signature': '4/4',
        'swing_dna': 0.07  # Very similar swing
    }
    
    # Test 2: Meter Clash (4/4 vs 3/4)
    clash_track = {
        'title': 'Clashing 3/4',
        'bpm': 124.0,
        'key': '1A',
        'time_signature': '3/4',
        'swing_dna': 0.05
    }
    
    # Test 3: Swing Difference
    swing_clash_track = {
        'title': 'Swing Clash',
        'bpm': 124.0,
        'key': '1A',
        'time_signature': '4/4',
        'swing_dna': 0.6  # High swing
    }

    # Setup track_data tuple mock
    # (track, current_track, current_bpm, min_energy, max_energy, phase_name, sorted_tracks, is_boutique)
    
    print("\n[Case 1] Matching Meter & Groove:")
    res1 = _calculate_candidate_score((good_track, current_track, 124.0, 0, 100, "Peak", [], False))
    print(f"Score: {res1[0]}")
    for trace in res1[2].get('audit_trace', []):
        if 'Meter' in trace['dim'] or 'Groove' in trace['dim']:
            print(f"  - {trace['dim']}: {trace['score']} ({trace['reason']})")

    print("\n[Case 2] Meter Clash (4/4 vs 3/4):")
    res2 = _calculate_candidate_score((clash_track, current_track, 124.0, 0, 100, "Peak", [], False))
    print(f"Score: {res2[0]}")
    for trace in res2[2].get('audit_trace', []):
        if 'Meter' in trace['dim']:
            print(f"  - {trace['dim']}: {trace['score']} ({trace['reason']})")

    print("\n[Case 3] Swing DNA Mismatch:")
    res3 = _calculate_candidate_score((swing_clash_track, current_track, 124.0, 0, 100, "Peak", [], False))
    print(f"Score: {res3[0]}")
    for trace in res3[2].get('audit_trace', []):
        if 'Groove' in trace['dim']:
            print(f"  - {trace['dim']}: {trace['score']} ({trace['reason']})")

    print("\n[Case 4] Boutique Rejection (Meter Clash):")
    res4 = _calculate_candidate_score((clash_track, current_track, 124.0, 0, 100, "Peak", [], True))
    print(f"Boutique Score: {res4[0]} (Should be very negative/-600000 range)")
    print(f"Rejected reason: {res4[2].get('boutique_rejected')}")

if __name__ == "__main__":
    test_rhythmic_scoring()
