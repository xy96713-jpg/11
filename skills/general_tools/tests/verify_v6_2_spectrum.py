import sys
import os
from pathlib import Path

# Add core dir to sys.path
sys.path.append(str(Path("d:/anti")))

try:
    from enhanced_harmonic_set_sorter import _calculate_candidate_score
except ImportError:
    import enhanced_harmonic_set_sorter
    _calculate_candidate_score = enhanced_harmonic_set_sorter._calculate_candidate_score

def test_spectral_scoring():
    print("=== V6.2 Spectral Masking Verification ===")
    
    # Base track with moderate energy
    current_track = {
        'title': 'Neutral Track',
        'bpm': 124.0,
        'key': '1A',
        'time_signature': '4/4',
        'swing_dna': 0.0,
        'spectral_bands': {
            'sub_bass': 0.3,
            'mid_range': 0.4,
            'high_presence': 0.2
        },
        'tonal_balance_low': 0.3, # Supporting factors
        'tonal_balance_mid': 0.4,
        'tonal_balance_high': 0.2
    }
    
    # Case 1: Sub-Bass Clash
    # Two tracks with high sub-bass should trigger the penalty
    bass_heavy_current = {
        **current_track,
        'spectral_bands': {**current_track['spectral_bands'], 'sub_bass': 0.7}
    }
    bass_heavy_candidate = {
        'title': 'Bass Heavy Candidate',
        'bpm': 124.0, 'key': '1A', 'time_signature': '4/4', 'swing_dna': 0.0,
        'spectral_bands': {'sub_bass': 0.75, 'mid_range': 0.4, 'high_presence': 0.2}
    }
    
    # Case 2: Mid-Range Masking (Muddy Mix)
    # Dense mids in both
    muddy_candidate = {
        'title': 'Mid Dense Candidate',
        'bpm': 124.0, 'key': '1A', 'time_signature': '4/4', 'swing_dna': 0.0,
        'spectral_bands': {'sub_bass': 0.2, 'mid_range': 0.8, 'high_presence': 0.1}
    }
    mid_dense_current = {
        **current_track,
        'spectral_bands': {**current_track['spectral_bands'], 'mid_range': 0.8}
    }

    print("\n[Case 1] Sub-Bass Clash Detection:")
    res1 = _calculate_candidate_score((bass_heavy_candidate, bass_heavy_current, 124.0, 0, 100, "Peak", [], False))
    # Correcting for how scores are aggregated (mi_score * 0.3 + trace penalty)
    found_clash = any('Bass Clash' in t['reason'] or 'bass_clash' in t['dim'] for t in res1[2].get('audit_trace', []))
    print(f"Audit Trace result for Bass Clash: {'PASSED' if found_clash else 'FAILED'}")
    for trace in res1[2].get('audit_trace', []):
        if 'Spectral' in trace['dim']:
            print(f"  - {trace['dim']}: {trace['score']} ({trace['reason']})")

    print("\n[Case 2] Mid-Range Masking Audit:")
    res2 = _calculate_candidate_score((muddy_candidate, mid_dense_current, 124.0, 0, 100, "Peak", [], False))
    mi_score = res2[2].get('mi_score', 0)
    print(f"MI Score with Mid Overlap: {mi_score:.1f}")
    # Expected lower vibe_balance in mi_details
    vibe_balance = res2[2].get('mi_details', {}).get('vibe_balance', '')
    print(f"  - Vibe Balance (MI Detail): {vibe_balance}")

if __name__ == "__main__":
    test_spectral_scoring()
