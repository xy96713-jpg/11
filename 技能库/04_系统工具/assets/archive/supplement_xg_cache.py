import os
import sys
import json
import glob

# Add path to import strict_bpm_multi_set_sorter
sys.path.insert(0, r"d:\anti\core")
try:
    from strict_bpm_multi_set_sorter import deep_analyze_track
    CACHE_FILE = r"d:\anti\song_analysis_cache.json"
except ImportError:
    # Fallback if path is different
    sys.path.insert(0, r"d:\anti")
    from core.strict_bpm_multi_set_sorter import deep_analyze_track
    CACHE_FILE = r"d:\anti\song_analysis_cache.json"

SEARCH_ROOTS = [r"d:\song", r"d:\song\kpop", r"C:\Users\Administrator\Downloads"]
TARGET_KEYWORDS = [
    "Gala",
    "Take My Breath",
    "Hypnotize",
    "4 SEASONS", 
    "PS118"
]

def find_files():
    found_files = {} # keyword -> list of paths
    
    print("Scanning for files...")
    for root_dir in SEARCH_ROOTS:
        if not os.path.exists(root_dir):
            continue
            
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if not file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                    continue
                    
                for kw in TARGET_KEYWORDS:
                    if kw.lower() in file.lower():
                        if kw not in found_files:
                            found_files[kw] = []
                        path = os.path.join(root, file)
                        if path not in found_files[kw]:
                            found_files[kw].append(path)
                            
    return found_files

def analyze_and_update(found_files):
    print(f"Loading cache from {CACHE_FILE}...")
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except:
        cache = {}
        
    updated_count = 0
    
    for kw, paths in found_files.items():
        print(f"\nTarget: {kw}")
        for path in paths:
            print(f"  Analyzing: {path}")
            # Run deep analysis
            # We don't have db_bpm here, so pass None. The function will use detection.
            try:
                # Check if already in cache with full analysis?
                # User asked to supplement, so we force analysis or check if it's missing dimensions.
                
                # Calculate hash key roughly (or just rely on update_cache inside deep_analyze not saving? 
                # deep_analyze returns the dict, we need to save it.)
                # Actually, strictly speaking, deep_analyze_track doesn't save to the main big json file itself 
                # unless we write a wrapper or if it uses the singleton cache manager.
                # In this codebase, strict_bpm_multi_set_sorter usually handles loading/saving.
                # Let's see if we can just update the cache dict and save it.
                
                analysis_result = deep_analyze_track(path)
                
                if analysis_result:
                    # We need to compute the hash key to save it into our local 'cache' dict for saving
                    # But deep_analyze_track might use a different hashing method.
                    # Let's try to reuse the existing cache keys if possible, or generate new one.
                    # For simplicty, looking at previous code, `get_file_hash` is used.
                    
                    # We will rely on strict_bpm_multi_set_sorter's internal logic if it saves?
                    # No, usually it returns the dict.
                    
                    # Let's import get_file_hash
                    from strict_bpm_multi_set_sorter import get_file_hash
                    file_hash = get_file_hash(path)
                    
                    cache[file_hash] = {
                        "path": path,
                        "analysis": analysis_result,
                        "timestamp": 20250122 # Fake timestamp or current
                    }
                    updated_count += 1
                    print(f"    [OK] BPM: {analysis_result.get('bpm')} | Key: {analysis_result.get('key')}")
                else:
                    print("    [Failed] Analysis returned None")
            except Exception as e:
                print(f"    [Error] {e}")

    if updated_count > 0:
        print(f"\nSaving {updated_count} updates to cache...")
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print("Cache updated successfully.")
    else:
        print("\nNo updates made.")

if __name__ == "__main__":
    found = find_files()
    if not found:
        print("No matching files found for the target keywords.")
    else:
        print(f"Found matches for {len(found)}/{len(TARGET_KEYWORDS)} keywords.")
        analyze_and_update(found)
