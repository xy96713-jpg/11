
import os
import sys
import json
from pathlib import Path
from typing import List, Dict

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # d:/anti/
sys.path.insert(0, str(BASE_DIR))

try:
    from core.cache_manager import load_cache, save_cache_atomic
    from core.audio_cortex import cortex
except ImportError:
    # Fallback if core is treated as a top-level module (if d:/anti/core is in path)
    sys.path.insert(0, str(BASE_DIR / "core"))
    from cache_manager import load_cache, save_cache_atomic
    from audio_cortex import cortex

def enrich_cache(file_list: List[str] = None, force_refresh: bool = False):
    """
    Enriches the global song_analysis_cache with Sonic DNA tags.
    """
    cache = load_cache()
    print(f"🚀 Sonic Enrichment Worker started. Cache size: {len(cache)}")
    
    # If file_list is provided, we need to map paths to cache keys or create new entries
    if file_list:
        actual_targets = []
        for f in file_list:
            f_norm = str(Path(f)).replace('\\', '/')
            # Find in cache
            found = False
            for k, v in cache.items():
                if isinstance(v, dict) and str(Path(v.get('file_path', ''))).replace('\\', '/') == f_norm:
                    actual_targets.append(k)
                    found = True
                    break
            if not found:
                print(f"⚠️ Track not found in cache: {f}. Skipping (Worker only enriches existing cache).")
        targets = actual_targets
    else:
        targets = list(cache.keys())
    
    enriched_count = 0
    
    for key in targets:
        entry = cache.get(key)
        if not entry or not isinstance(entry, dict):
            continue
            
        file_path = entry.get('file_path')
        if not file_path or not os.path.exists(file_path):
            continue
            
        analysis = entry.get('analysis', {})
        
        # Check if already enriched
        if not force_refresh and 'sonic_dna' in analysis:
            continue
            
        print(f"🔊 Analyzing Timbre: {os.path.basename(file_path)}...")
        
        try:
            # 1. Get tags from AudioCortex
            # analyze_track returns a dict with 'instruments'
            tags_data = cortex.analyze_track(file_path, force_refresh=force_refresh)
            
            if tags_data:
                # 2. Inject into cache
                analysis.update(tags_data) # Sync all DSP fields (sonic_dna, arousal_proxy, bpm, etc.)
                if 'instruments' in tags_data:
                    analysis['sonic_dna'] = tags_data['instruments']
                
                entry['analysis'] = analysis
                enriched_count += 1
                
                # Save every 5 tracks to prevent data loss or if it's the only one
                if enriched_count % 5 == 0:
                    save_cache_atomic(cache)
                    print(f"💾 Cache periodic save: {enriched_count} tracks enriched.")
                    
        except Exception as e:
            print(f"❌ Failed to enrich {file_path}: {e}")

    # Final save
    if enriched_count > 0:
        save_cache_atomic(cache)
        print(f"✅ Enrichment complete! Total enriched: {enriched_count}")
    else:
        print("ℹ️ No new tracks needed enrichment.")

if __name__ == "__main__":
    # Example: Run on specific items if needed
    # Usage: python sonic_enrichment_worker.py
    import argparse
    parser = argparse.ArgumentParser(description="Sonic Enrichment Worker")
    parser.add_argument("--files", nargs="+", help="Specific files to enrich")
    parser.add_argument("--force", action="store_true", help="Force re-analysis")
    args = parser.parse_args()
    
    enrich_cache(file_list=args.files, force_refresh=args.force)
