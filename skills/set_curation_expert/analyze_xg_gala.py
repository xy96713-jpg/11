import hashlib
import sys
import json
import os

# Add path
sys.path.insert(0, r"d:\anti\core")
try:
    from strict_bpm_multi_set_sorter import deep_analyze_track
    CACHE_FILE = r"d:\anti\song_analysis_cache.json"
except ImportError:
    sys.path.insert(0, r"d:\anti")
    from core.strict_bpm_multi_set_sorter import deep_analyze_track
    CACHE_FILE = r"d:\anti\song_analysis_cache.json"

def get_file_hash(file_path):
    """Calculate SHA1 hash of file"""
    import hashlib
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

TARGET_FILE = r"d:\song\kpop\XG - GALA.mp3"

def main():
    if not os.path.exists(TARGET_FILE):
        print(f"Error: Target file not found: {TARGET_FILE}")
        return

    print(f"Analyzing {TARGET_FILE}...")
    try:
        # Load existing cache
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            
        # Analyze
        analysis = deep_analyze_track(TARGET_FILE)
        
        if analysis:
            file_hash = get_file_hash(TARGET_FILE)
            cache[file_hash] = {
                "path": TARGET_FILE,
                "analysis": analysis,
                "hashed_at": 20250122 # Just a marker
            }
            
            # Save
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
                
            print(f"Success! Updated cache for XG - GALA.mp3")
            print(f"BPM: {analysis.get('bpm')}, Key: {analysis.get('key')}")
            
    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == "__main__":
    main()
