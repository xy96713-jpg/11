
import sys
import os

# Adjust path to find enhanced_harmonic_set_sorter
sys.path.append("d:/anti")

try:
    from enhanced_harmonic_set_sorter import _calculate_candidate_score
except ImportError:
    print("Error: Could not import _calculate_candidate_score from enhanced_harmonic_set_sorter")
    sys.exit(1)

def test_lufs_swing_audit():
    print("--- Testing LUFS and Swing Audit Logic ---")
    
    # Mock Current Track (Normal)
    current_track = {
        'title': 'Current Track',
        'bpm': 120.0,
        'key': '8A',
        'energy': 50,
        'loudness_lufs': -10.0,
        'swing_dna': 0.0
    }
    
    # Mock Next Track (Issues: 5dB drop, High Swing)
    next_track = {
        'title': 'Next Track (Problematic)',
        'bpm': 120.0,
        'key': '8A',
        'energy': 50,
        'loudness_lufs': -15.0, # Diff 5.0 -> Should trigger LUFS penalty
        'swing_dna': 0.4        # Diff 0.4 -> Should trigger Swing penalty
    }
    
    # Mock arguments for _calculate_candidate_score
    # track_data: (track, current_track, current_bpm, min_energy, max_energy, phase_name, sorted_tracks, is_boutique)
    track_data = (
        next_track,
        current_track,
        120.0, # current_bpm
        40,    # min_energy
        60,    # max_energy
        "Peak",# phase_name
        [],    # sorted_tracks
        False  # is_boutique
    )
    
    # Run calculation
    score, track, metrics = _calculate_candidate_score(track_data)
    
    print(f"\nFinal Score: {score}")
    print("\nAudit Trace:")
    found_lufs = False
    found_swing = False
    
    if 'audit_trace' in metrics:
        for trace in metrics['audit_trace']:
            print(f"  - [{trace['dim']}] Score: {trace['score']}, Val: {trace['val']}, Reason: {trace['reason']}")
            if "Acoustics (LUFS)" in trace['dim']:
                found_lufs = True
            if "Rhythm (Swing)" in trace['dim']:
                found_swing = True
                
    print("\nVerification Results:")
    print(f"  LUFS Trace Found: {found_lufs}")
    print(f"  Swing Trace Found: {found_swing}")
    
    if found_lufs and found_swing:
        print("\n✅ SUCCESS: Both V6.1 features are correctly audited!")
    else:
        print("\n❌ FAILURE: Missing audit traces.")

if __name__ == "__main__":
    test_lufs_swing_audit()
