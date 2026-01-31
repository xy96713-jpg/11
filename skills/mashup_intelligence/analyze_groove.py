import json
from pathlib import Path

def analyze_groove_compatibility():
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
        print("忍者 not found")
        return

    n_a = ninja.get('analysis', {})
    print(f"--- 忍者 (Ninja) Groove DNA ---")
    print(f"Swing DNA: {n_a.get('swing_dna')}")
    print(f"Drum Pattern: {n_a.get('drum_pattern')}")
    print(f"Percussive Ratio: {n_a.get('energy_profile', {}).get('percussive_ratio')}")
    print(f"Onset Density: {n_a.get('onset_density')}")
    print(f"Pulse Clarity: {n_a.get('pulse_clarity')}")

    # 寻找律动匹配者
    keywords = ['afro', 'jersey', 'trap', 'kanye', 'kendrick', 'baile', 'amapiano']
    print(f"\n--- Top Groove Matches (Syncopation & Swing) ---")
    
    candidates = []
    for v in cache.values():
        if v.get('file_path') == ninja_path: continue
        a = v.get('analysis', {})
        
        # 律动相关得分
        swing_diff = abs(a.get('swing_dna', 0) - n_a.get('swing_dna', 0))
        density_diff = abs(a.get('onset_density', 0) - n_a.get('onset_density', 0))
        
        # 综合律动分 (越高越契合)
        groove_score = (1.0 - swing_diff) * 40 + (1.0 - (density_diff/5.0)) * 60
        
        title = v.get('title', 'Unknown')
        artist = v.get('artist', 'Unknown')
        if any(k in str(v).lower() for k in keywords):
            candidates.append({
                'title': title,
                'artist': artist,
                'score': groove_score,
                'swing': a.get('swing_dna'),
                'pattern': a.get('drum_pattern'),
                'path': v.get('file_path')
            })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    for c in candidates[:10]:
        print(f"[{c['score']:.1f}] {c['title']} - {c['artist']}")
        print(f"  Swing: {c['swing']}, Pattern: {c['pattern']}")
        print(f"  Path: {c['path']}")

if __name__ == "__main__":
    analyze_groove_compatibility()
