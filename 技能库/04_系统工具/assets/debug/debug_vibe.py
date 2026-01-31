import json
from pathlib import Path

def debug_vibe_matches():
    cache_path = Path("d:/anti/song_analysis_cache.json")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    ninja_path = "D:/song/周杰伦/2001-范特西/周杰伦 - 忍者.flac"
    ninja = None
    for v in cache.values():
        if v.get('file_path') == ninja_path:
            ninja = v
            break
    
    if not ninja:
        print("忍者 not found in cache")
        return

    keywords = ['kanye', 'afro', 'jersey', 'travis', 'scott', 'dna', 'wap', 'power']
    vibe_tracks = []
    for v in cache.values():
        p = v.get('file_path', '').lower()
        if any(k in p for k in keywords):
            vibe_tracks.append(v)

    print(f"--- Ninja Analysis ---")
    n_a = ninja.get('analysis', {})
    print(f"BPM: {n_a.get('bpm')}, Key: {n_a.get('key')}, Onset: {n_a.get('onset_density')}, Busy: {n_a.get('busy_score')}")

    print(f"\n--- Potential Vibe Pairs ---")
    for v in vibe_tracks:
        a = v.get('analysis', {})
        print(f"Track: {v.get('title')} ({v.get('artist')})")
        print(f"  Path: {v.get('file_path')}")
        print(f"  BPM: {a.get('bpm')}, Key: {a.get('key')}, Onset: {a.get('onset_density')}, Busy: {a.get('busy_score')}")
        print("-" * 30)

if __name__ == "__main__":
    debug_vibe_matches()
