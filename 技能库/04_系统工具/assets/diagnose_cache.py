import json
import os
from collections import Counter

CACHE_FILE = r"d:\anti\song_analysis_cache.json"

def diagnose_cache_v2():
    if not os.path.exists(CACHE_FILE):
        print("Cache file not found.")
        return

    print(f"Loading cache from {CACHE_FILE}...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    total_entries = len(cache)
    print(f"Total entries (Hashes): {total_entries}")

    exist_count = 0
    missing_count = 0
    duplicate_path_count = 0
    
    # Analyze paths
    path_map = {} # path -> list of hashes
    folder_counter = Counter()
    
    for key, entry in cache.items():
        # Try to find the path in the entry
        # Structure might be entry['path'] or entry['file_path']
        file_path = entry.get('path') or entry.get('file_path') or entry.get('analysis', {}).get('file_path')
        
        if not file_path:
            # Maybe it's just the key? No, keys explain hashes.
            continue
            
        if file_path not in path_map:
            path_map[file_path] = []
        path_map[file_path].append(key)
        
        folder = os.path.dirname(file_path)
        folder_counter[folder] += 1

    # Check existence of unique paths
    unique_paths = list(path_map.keys())
    print(f"Unique File Paths Found: {len(unique_paths)}")
    
    for p in unique_paths:
        if os.path.exists(p):
            exist_count += 1
        else:
            missing_count += 1
            
    print(f"\n===== Cache Health Diagnosis V2 =====")
    print(f"Total Cache Entries (Hashes) : {total_entries}")
    print(f"Unique File Paths            : {len(unique_paths)}")
    print(f"  - Existing on Disk         : {exist_count}")
    print(f"  - Missing / Ghosts         : {missing_count}")
    
    # Check for duplicates (same path, multiple hashes - implies file changed or re-hashed)
    multi_hash_paths = {p: hashes for p, hashes in path_map.items() if len(hashes) > 1}
    print(f"Paths with multiple hash entries: {len(multi_hash_paths)}")
    
    print(f"\n[Top Source Folders]")
    for folder, count in folder_counter.most_common(10):
        print(f"  {count:4d} | {folder}")

    if missing_count > 0:
        print(f"\n[Sample Missing Files] (Paths in cache but not on disk)")
        for p in unique_paths:
            if not os.path.exists(p):
                print(f"  - {p}")
                missing_count -= 1
                if missing_count < (len(unique_paths) - 5): # Just show 5
                    break
                    
if __name__ == "__main__":
    diagnose_cache_v2()
