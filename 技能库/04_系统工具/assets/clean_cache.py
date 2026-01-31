import json
import os
from datetime import datetime

CACHE_FILE = r"d:\anti\song_analysis_cache.json"
BACKUP_FILE = r"d:\anti\song_analysis_cache.json.bak"

def clean_cache():
    if not os.path.exists(CACHE_FILE):
        print("Cache file not found.")
        return

    print(f"Loading cache from {CACHE_FILE}...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    initial_count = len(cache)
    print(f"Initial entries: {initial_count}")

    # Create a map of file_path -> (hash, timestamp/entry)
    # We want to keep the "best" or "latest" entry for each path.
    # Since we don't have explicit timestamps in all entries, we'll assume the one with the most data is best,
    # or just pick one if identical.
    
    unique_map = {} # path -> (key, entry)
    
    for key, entry in cache.items():
        file_path = entry.get('path') or entry.get('file_path') or entry.get('analysis', {}).get('file_path')
        
        if not file_path:
            continue
            
        # Normalize path
        norm_path = os.path.normpath(file_path).lower()
        
        current_data_size = len(json.dumps(entry))
        
        if norm_path not in unique_map:
            unique_map[norm_path] = (key, entry)
        else:
            # Conflict: compare quality/timestamp
            existing_key, existing_entry = unique_map[norm_path]
            existing_size = len(json.dumps(existing_entry))
            
            # Simple heuristic: keep the one with more data (likely newer/more complete analysis)
            if current_data_size > existing_size:
                unique_map[norm_path] = (key, entry)
                
    # Reconstruct clean cache
    new_cache = {}
    for path, (key, entry) in unique_map.items():
        if os.path.exists(entry.get('path') or entry.get('file_path') or ""):
             new_cache[key] = entry
        else:
            # Double check existence using the key in map
            # Actually, `unique_map` relied on path.
            # Let's verify file existence one last time to purge ghosts
             original_path = entry.get('path') or entry.get('file_path')
             if original_path and os.path.exists(original_path):
                 new_cache[key] = entry

    final_count = len(new_cache)
    print(f"Cleaned entries: {final_count}")
    print(f"Removed {initial_count - final_count} duplicates/ghosts.")

    # Save
    import shutil
    shutil.copy2(CACHE_FILE, BACKUP_FILE)
    print(f"Backup saved to {BACKUP_FILE}")
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_cache, f, indent=2, ensure_ascii=False)
    print("Cache saved successfully.")

if __name__ == "__main__":
    clean_cache()
