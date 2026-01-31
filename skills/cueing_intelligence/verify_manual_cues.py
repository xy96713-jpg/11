from enhanced_harmonic_set_sorter import generate_transition_advice

def test_transition_guard_scenarios():
    print("\n--- Transition Guard Scenarios Test ---")

    # Scenario 1: AI-Ghost Windowing (Track 1 has manual C/D, Track 2 has none)
    track1 = {'title': 'T1', 'hotcue_C': 100, 'hotcue_D': 130, 'exit_bars': 16, 'bpm': 128}
    track2 = {'title': 'T2', 'mix_in_point': 5.0, 'bpm': 128} # No hotcue_A
    
    advice1 = generate_transition_advice(track1, track2, 1)
    print("\nScenario 1 (Ghost Window):")
    for line in advice1: print(line)
    assert any("建议下一首在该长度前开始进场" in l for l in advice1)
    assert any("AI 匹配：已自动将下一首 A点 锚定在 AI Mix-In" in l for l in advice1)

    # Scenario 2: Phrase-Shift Warning (Manual A is NOT at a phrase start)
    track3 = {'title': 'T3', 'bpm': 128}
    # Mock structure with points at 0, 15, 30...
    track4 = {
        'title': 'T4', 
        'bpm': 128, 
        'hotcue_A': 7.5, # Offset by half a phrase (assuming 4 beats = 1.875s @ 128bpm)
        'structure': {'structure': {'intro': [0, 15, 30]}}
    }
    
    advice2 = generate_transition_advice(track3, track4, 2)
    print("\nScenario 2 (Phrase-Shift):")
    for line in advice2: print(line)
    assert any("乐句偏移：手动A点未对齐 AI 乐句起始点" in l for l in advice2)

    print("\nSUCCESS: All Big-Brain 'Transition Guard' scenarios verified!")

if __name__ == "__main__":
    test_transition_guard_scenarios()
