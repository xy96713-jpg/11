import sys
import os
from pathlib import Path
import numpy as np

# 设置导入路径
BASE_DIR = Path(r"d:\anti")
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "skills"))

from strict_bpm_multi_set_sorter import analyze_mix_metrics_light
import librosa

def test_v3_extraction():
    test_file = r"D:/song/huayu_songs/周杰伦本草纲目.mp3"
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return

    print("--- 正在测试 V3-PRO 特征提取 ---")
    y, sr = librosa.load(test_file, sr=22050, duration=30)
    # 模拟 beat_times
    beat_times = np.arange(0, 30, 0.6) # 100 BPM
    
    res = analyze_mix_metrics_light(y, sr, 100.0, beat_times, test_file)
    
    v3_keys = ["spectral_bands", "swing_dna", "energy_curve", "timbre_texture"]
    for key in v3_keys:
        if key in res:
            print(f"✅ 成功找到维度: {key}")
            print(f"   样例数据: {res[key]}")
        else:
            print(f"❌ 未找到维度: {key}")

if __name__ == "__main__":
    test_v3_extraction()
