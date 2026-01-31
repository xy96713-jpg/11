import json
from pathlib import Path

def compare_dna():
    cache_path = Path("d:/anti/song_analysis_cache.json")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    ninja_path = "D:/song/周杰伦/2001-范特西/周杰伦 - 忍者.flac"
    sjg_path = "D:/song/周杰伦/2001-范特西/周杰伦 - 双截棍.flac"
    
    ninja = None
    sjg = None
    for v in cache.values():
        if v.get('file_path') == ninja_path: ninja = v
        if v.get('file_path') == sjg_path: sjg = v

    if not ninja or not sjg:
        print("忍者 or 双截棍 not found in cache")
        return

    n_a = ninja.get('analysis', {})
    s_a = sjg.get('analysis', {})

    print(f"{'Metric':<20} | {'忍者':<20} | {'双截棍':<20}")
    print("-" * 65)
    print(f"{'BPM':<20} | {n_a.get('bpm'):<20} | {s_a.get('bpm'):<20}")
    print(f"{'Key':<20} | {n_a.get('key'):<20} | {s_a.get('key'):<20}")
    print(f"{'Onset Density':<20} | {n_a.get('onset_density'):<20} | {s_a.get('onset_density'):<20}")
    print(f"{'Timbre Complexity':<20} | {n_a.get('timbre_texture', {}).get('complexity'):<20} | {s_a.get('timbre_texture', {}).get('complexity'):<20}")
    
    n_tb = n_a.get('tonal_balance_mid', 0)
    s_tb = s_a.get('tonal_balance_mid', 0)
    print(f"{'Tonal Balance Mid':<20} | {n_tb:<20} | {s_tb:<20}")

    print(f"\nTags Ninja: {ninja.get('tags', [])}")
    print(f"Tags SJG: {sjg.get('tags', [])}")

if __name__ == "__main__":
    compare_dna()
