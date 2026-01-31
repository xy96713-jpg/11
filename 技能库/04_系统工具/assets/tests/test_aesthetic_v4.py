import sys
from pathlib import Path

# 设置环境路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "skills"))

from enhanced_harmonic_set_sorter import _calculate_candidate_score, generate_transition_advice, AESTHETIC_ENABLED
import json

def test_aesthetic_integration():
    print(f"--- [Aesthetic-V4 集成验证] ---")
    print(f"美学引擎开启状态: {AESTHETIC_ENABLED}")
    
    # 场景 1: 非常兼容的流派与情感 (Deep House -> Melodic Techno)
    track1 = {
        'title': 'Deep Sunset',
        'genre': 'Deep House',
        'energy': 45,
        'vocal_ratio': 0.2,
        'kick_drum_power': 0.6,
        'key': '8A',
        'bpm': 122.0
    }
    
    track2 = {
        'title': 'Ethereal Voyage',
        'genre': 'Melodic Techno',
        'energy': 65,
        'vocal_ratio': 0.1,
        'kick_drum_power': 0.7,
        'key': '8A',
        'bpm': 124.0
    }
    
    # 模拟 Sorter 评分
    print("\n[Case 1] 验证跨流派兼容性 (Deep House -> Melodic Techno)")
    track_data = (track2, track1, 122.0, 40, 70, "Build-up", [], False)
    score, track_res, metrics = _calculate_candidate_score(track_data)
    
    print(f"审美分 (ae_score): {metrics.get('ae_score')}")
    print(f"审美细节: {metrics.get('ae_details')}")
    
    # 场景 2: 风格突变 (Ambient -> Dubstep)
    track3 = {
        'title': 'Space Noise',
        'genre': 'Ambient',
        'energy': 20,
        'vocal_ratio': 0,
        'key': '1A',
        'bpm': 100
    }
    
    track4 = {
        'title': 'Chaos Bass',
        'genre': 'Dubstep',
        'energy': 90,
        'vocal_ratio': 0.1,
        'key': '1A',
        'bpm': 140
    }
    
    print("\n[Case 2] 验证风格对冲惩罚 (Ambient -> Dubstep)")
    track_data_clash = (track4, track3, 100.0, 10, 100, "Peak", [], False)
    score_clash, _, metrics_clash = _calculate_candidate_score(track_data_clash)
    print(f"审美分 (ae_score): {metrics_clash.get('ae_score')}")
    print(f"审美细节: {metrics_clash.get('ae_details')}")

    # 场景 3: 混音建议审计
    print("\n[Case 3] 审计“混音圣经”报告...")
    advice = generate_transition_advice(track1, track2, 1)
    for line in advice:
        if "🎨" in line or "•" in line:
            print(line)

if __name__ == "__main__":
    test_aesthetic_integration()
