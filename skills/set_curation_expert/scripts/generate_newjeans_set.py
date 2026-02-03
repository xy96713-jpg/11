import sys
from pathlib import Path
import json
import asyncio
import os

# 设置路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp")) # [V35.21] Fix Import
sys.path.insert(0, str(BASE_DIR / "skills"))

from rekordbox_mcp.database import RekordboxDatabase
from rekordbox_mcp.models import SearchOptions # Import SearchOptions

try:
    from core.harmonic_utils import get_key_compatibility_flexible
except ImportError:
    # Fallback or debug
    print(f"DEBUG IMPORTS: {sys.path}")
    from core.harmonic_utils import get_key_compatibility_flexible

from core.cache_manager import load_cache

# CACHE_FILE = BASE_DIR / "song_analysis_cache.json" # Deprecated
OUTPUT_DIR = Path("D:/生成的set")

async def generate_set():
    print("🚀 [NewJeans Set Generator] Initializing...")
    
    # 1. DB Fetch
    db = RekordboxDatabase()
    await db.connect()
    
    print("🔎 Searching for NewJeans tracks...")
    all_tracks = await db.search_tracks(SearchOptions(query="NewJeans")) # Fuzzy search via Object
    if not all_tracks:
        all_tracks = await db.search_tracks("New Jeans")
    
    # 2. Cache Enrichment
    cache = load_cache()
    
    enriched_tracks = []
        
    enriched_tracks = []
    for t in all_tracks:
        # Check Artist
        if "NEWJEANS" not in t.artist.upper() and "NEWJEANS" not in t.title.upper():
            continue
            
        # Get Analysis
        analysis = {}
        entry = cache.get(t.file_path)
        if entry and 'analysis' in entry:
            analysis = entry['analysis']
        else:
            # Fallback (Metadata)
            analysis = {
                'bpm': t.bpm,
                'key': t.key,
                'energy': 50.0,
                'sonic_dna': ['Pop'] # Default
            }
            
        # Ensure Critical Data
        if not analysis.get('bpm'): analysis['bpm'] = t.bpm or 130.0
        if not analysis.get('key'): analysis['key'] = t.key or "1A"
            
        enriched_tracks.append({
            'track_info': t,
            'analysis': analysis
        })
        
    print(f"✅ Found {len(enriched_tracks)} NewJeans tracks.")
    
    if len(enriched_tracks) < 3:
        print("❌ Not enough tracks to generate a set.")
        return

    # 3. Sorter (Simple Rising Energy & Harmonic)
    # Start with lowest BPM
    enriched_tracks.sort(key=lambda x: x['analysis']['bpm'])
    
    # Optimization: If we have many, try to chain keys. But for now, simple BPM rise is robust.
    final_set = enriched_tracks
    
    # 4. Generate Report (Traceability)
    report_path = OUTPUT_DIR / "NewJeans_Set_Comparison.md"
    
    # Helper for Matrix
    def format_traceability_data(t_data, prefix=""):
        lines = []
        # Flatten dictionary
        def flatten(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = parent_key + sep + k if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    if len(v) > 0 and isinstance(v[0], (int, float)) and len(v) > 10:
                        for i, val in enumerate(v):
                             items.append((f"{new_key}_{i:02d}", val))
                    else:
                        items.append((new_key, v))
                else:
                    items.append((new_key, v))
            return dict(items)
            
        ana = t_data.get('analysis', {})
        t_info = t_data.get('track_info')
        # Create a dict from track_info object
        info_dict = {'id': t_info.id, 'title': t_info.title, 'artist': t_info.artist, 'path': t_info.file_path}
        
        full_data = {**{"META_"+k:v for k,v in info_dict.items()}, **ana}
        flat_data = flatten(full_data)
        sorted_keys = sorted(flat_data.keys())
        
        lines.append(f"#### 🧬 {prefix} Traceability Matrix ({len(sorted_keys)} Dimensions)")
        lines.append("| Dimension ID | Value | Category |")
        lines.append("| :--- | :--- | :--- |")
        
        for k in sorted_keys:
            val = flat_data[k]
            # Categorize
            cat = "Metadata"
            if "mfcc" in k or "timbre" in k: cat = "Timbre/Spectral"
            elif "bpm" in k or "rhythm" in k or "beat" in k or "onset" in k: cat = "Rhythm/Timing"
            elif "key" in k or "chord" in k or "tonal" in k: cat = "Harmonic/Tonal"
            elif "energy" in k or "loudness" in k or "arousal" in k: cat = "Energy/Dynamics"
            elif "tags" in k or "genre" in k or "dna" in k: cat = "Semantic/Tags"
            
            val_str = str(val)
            if len(val_str) > 100: val_str = val_str[:97] + "..."
            val_str = val_str.replace("|", "/")
            lines.append(f"| `{k}` | {val_str} | {cat} |")
        return "\n".join(lines)

    from datetime import datetime
    generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# NewJeans Sonic DNA Set (System Comparison)\n\n")
        f.write(f"> **Generated**: {generation_time}\n")
        f.write(f"> **System Used**: V35.20 (Sonic DNA + Deep Reconstruction)\n")
        f.write(f"> **Total Tracks**: {len(final_set)}\n\n")
        
        f.write("## 🎵 Set Sequence\n\n")
        
        for i, t in enumerate(final_set):
            info = t['track_info']
            ana = t['analysis']
            f.write(f"### {i+1}. {info.title}\n")
            f.write(f"- **BPM**: {ana['bpm']} | **Key**: {ana['key']}\n")
            f.write(f"- **Sonic DNA**: `{ana.get('sonic_dna', [])}`\n")
            
            # Transition Advice
            if i < len(final_set) - 1:
                next_t = final_set[i+1]['analysis']
                bpm_diff = next_t['bpm'] - ana['bpm']
                f.write(f"> 🔄 **Transition**: Energy Rise (+{bpm_diff:.1f} BPM)\n")
            
            f.write("\n")
            
        f.write("---\n\n")
        f.write("## 📜 附录: 全维可溯源数据 (Technical Traceability)\n")
        f.write("> 以下展示每首曲目的全维度分析数据，证明系统的深度感知能力。\n\n")
        
        for i, t in enumerate(final_set):
            f.write(format_traceability_data(t, prefix=f"Track {i+1}: {t['track_info'].title}"))
            f.write("\n\n---\n\n")
            
    # 5. Generate M3U
    m3u_path = OUTPUT_DIR / "NewJeans_Sonic_Set.m3u"
    with open(m3u_path, "w", encoding="utf-8") as m3u:
        m3u.write("#EXTM3U\n")
        for t in final_set:
            info = t['track_info']
            m3u.write(f"#EXTINF:-1,[{info.key}] [{info.bpm}] {info.title}\n")
            m3u.write(f"{info.file_path}\n")
            
    print(f"✅ Report generated: {report_path}")
    print(f"✅ M3U generated: {m3u_path}")
    
    # Auto-open
    try:
        os.startfile(str(report_path))
    except:
        pass
        
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_set())
