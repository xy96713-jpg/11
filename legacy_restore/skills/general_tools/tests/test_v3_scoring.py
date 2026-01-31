import sys
import os
from pathlib import Path

# 设置导入路径
BASE_DIR = Path(r"d:\anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "skills"))

from skill_mashup_intelligence import MashupIntelligence

def test_v3_scoring():
    # 模拟两个带有 V3 特征的音轨数据
    # Track A: 周杰伦 - 本草纲目 (假设)
    track1 = {
        "track_info": {"title": "本草纲目"},
        "analysis": {
            "bpm": 100.88,
            "key": "D# Minor",
            "vocal_ratio": 0.8,
            "spectral_bands": {"mid_range": 0.3, "high_presence": 0.1},
            "swing_dna": 0.05 # 直板
        }
    }
    
    # Track B: Chanté Moore - Straight Up (假设)
    track2 = {
        "track_info": {"title": "Straight Up"},
        "analysis": {
            "bpm": 100.01,
            "key": "D# Minor",
            "vocal_ratio": 0.2, # 假设取伴奏层
            "spectral_bands": {"mid_range": 0.15, "high_presence": 0.05}, # 互补
            "swing_dna": 0.06 # 律动接近
        }
    }
    
    skill = MashupIntelligence()
    score, details = skill.calculate_mashup_score(track1, track2)
    
    print(f"--- V3-PRO 评分测试结果 ---")
    print(f"推荐组合: {track1['track_info']['title']} + {track2['track_info']['title']}")
    print(f"最终得分: {score:.1f}")
    if 'v3_pro' in details:
        print(f"✅ V3-PRO 维度生效: {details['v3_pro']}")
    else:
        print(f"❌ V3-PRO 维度未生效")

if __name__ == "__main__":
    test_v3_scoring()
