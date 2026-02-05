import librosa
import numpy as np
import json
import os

def audit_audio_physical_evidence(audio_path, start_sec, end_sec):
    print(f"[*] Analyzing physical evidence for: {audio_path} ({start_sec}s - {end_sec}s)")
    y, sr = librosa.load(audio_path, sr=16000, offset=start_sec, duration=end_sec-start_sec)
    
    # 1. RMS Energy (Volume)
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr) + start_sec
    
    # 2. Onset Strength (The "Kick" of the vocal)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # 3. Find Onsets (Physical Start Times)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time') + start_sec
    
    evidence = {
        "analysis_range": [start_sec, end_sec],
        "energy_peaks": [],
        "physical_onsets": onsets.tolist()
    }
    
    # Detect significant energy peaks (potential syllables)
    for i, e in enumerate(rms):
        if e > np.mean(rms) * 1.5:
            evidence["energy_peaks"].append({"time": float(times[i]), "energy": float(e)})
            
    with open("physical_audit_results.json", "w") as f:
        json.dump(evidence, f, indent=4)
        
    print(f"[+] Physical evidence captured in physical_audit_results.json")

if __name__ == "__main__":
    audio_file = r"d:\anti\技能库\10_字幕生成专家\Timeline 1_(Vocals)_UVR-MDX-NET-Voc_FT.wav"
    # Inspect the gap the user mentioned (around 1:00)
    audit_audio_physical_evidence(audio_file, 55, 75)
