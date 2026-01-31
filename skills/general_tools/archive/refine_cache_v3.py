import json
import os
import sys
from pathlib import Path
import numpy as np
import librosa

def analyze_v3_dimensions(file_path):
    """
    V3.0 Ultra+ 维度分析：
    - swing_ratio: 0.0 (Straight) -> 1.0 (Heavy Swing)
    - spectral_centroid: 声音明亮度
    - synthesis_type: 拟合音色类型 (Analog/Digital/Hybrid)
    """
    try:
        # 只加载前 60 秒进行分析，节约时间
        y, sr = librosa.load(file_path, duration=60)
        
        # 1. Spectral Centroid (明亮度)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_centroid = float(np.mean(centroid))
        
        # 2. Swing Ratio (律动比)
        # 寻找节拍
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        swing_score = 0.0
        if len(beat_times) > 8:
            # 计算每两个拍子之间的间隔比例
            intervals = np.diff(beat_times)
            # 简化逻辑：观察 1/8 音符的微移
            # 这里使用 librosa 的脉冲强度来检测 swing
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
            # 通过 tempogram 的谐波比判断 swing
            swing_score = float(np.mean(tempogram[1]) / (np.mean(tempogram[0]) + 1e-6))
            swing_score = min(max(swing_score, 0.0), 1.0)

        # 3. Synthesis Type (启发式预测)
        # 模拟分析：根据谐波丰富度定义
        harm = librosa.effects.harmonic(y)
        perc = librosa.effects.percussive(y)
        hp_ratio = np.mean(np.abs(harm)) / (np.mean(np.abs(perc)) + 1e-6)
        
        if avg_centroid > 3000:
            synth = "Digital/Wavetable"
        elif hp_ratio > 1.5:
            synth = "Analog/Subtractive"
        else:
            synth = "Hybrid/Natural"

        return {
            'swing_ratio': round(swing_score, 3),
            'spectral_centroid': round(avg_centroid, 2),
            'synthesis_type': synth,
            'v3_audit': True
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None

def main():
    cache_path = Path(r"d:\anti\song_analysis_cache.json")
    if not cache_path.exists():
        print("Cache not found.")
        return

    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    print(f"Total entries in cache: {len(cache)}")
    
    # 为了演示，只更新前 5 个未审计的条目
    count = 0
    for key, data in cache.items():
        if count >= 5: break
        
        analysis = data.get('analysis', {})
        if analysis.get('v3_audit'): continue
        
        file_path = data.get('file_path')
        if file_path and os.path.exists(file_path):
            print(f"Refining: {Path(file_path).name}")
            v3_data = analyze_v3_dimensions(file_path)
            if v3_data:
                analysis.update(v3_data)
                data['analysis'] = analysis
                count += 1
    
    if count > 0:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print(f"Successfully refined {count} entries with V3.0 Ultra+ dimensions.")

if __name__ == "__main__":
    main()
