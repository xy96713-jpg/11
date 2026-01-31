import sys
import os
from pathlib import Path

# Add core dir to sys.path
sys.path.append(str(Path("d:/anti")))

# Import production functions
try:
    from enhanced_harmonic_set_sorter import generate_transition_advice
except ImportError:
    import enhanced_harmonic_set_sorter
    generate_transition_advice = enhanced_harmonic_set_sorter.generate_transition_advice

def test_workflow_visibility():
    print("=== Testing V6.2 Workflow Visibility in Reports ===")
    
    # 1. Simulate Meter Clash (4/4 vs 3/4)
    t1 = {'title': '4/4 Track', 'bpm': 124.0, 'key': '1A', 'time_signature': '4/4', 'spectral_bands': {}}
    t2 = {'title': '3/4 Track', 'bpm': 124.0, 'key': '1A', 'time_signature': '3/4', 'spectral_bands': {}}
    
    print("\n[Scenario 1] Meter Clash Detection:")
    advice1 = generate_transition_advice(t1, t2, 0)
    found_meter = any("Meter Clash" in line for line in advice1)
    print(f"Meter Clash Advice present: {found_meter}")
    for line in advice1:
        if "Meter Clash" in line:
            print(f"  - {line.strip()}")

    # 2. Simulate Bass Clash (Spectral)
    # We need to ensure MASHUP_INTELLIGENCE is active during the test
    t3 = {
        'title': 'Heavy Bass 1', 'bpm': 124.0, 'key': '1A', 'time_signature': '4/4',
        'spectral_bands': {'sub_bass': 0.8, 'mid_range': 0.4, 'high_presence': 0.2},
        'tonal_balance_low': 0.8, 'tonal_balance_mid': 0.1, 'tonal_balance_high': 0.1
    }
    t4 = {
        'title': 'Heavy Bass 2', 'bpm': 124.0, 'key': '1A', 'time_signature': '4/4',
        'spectral_bands': {'sub_bass': 0.85, 'mid_range': 0.4, 'high_presence': 0.2},
        'tonal_balance_low': 0.85, 'tonal_balance_mid': 0.1, 'tonal_balance_high': 0.1
    }

    print("\n[Scenario 2] Bass Clash Detection:")
    advice2 = generate_transition_advice(t3, t4, 1)
    found_bass = any("频谱预警" in line or "Spectral" in line for line in advice2)
    print(f"Spectral Warning present: {found_bass}")
    for line in advice2:
        if "频谱预警" in line or "Spectral" in line:
            print(f"  - {line.strip()}")

if __name__ == "__main__":
    test_workflow_visibility()
