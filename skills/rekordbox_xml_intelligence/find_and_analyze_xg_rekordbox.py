import os
import sys
import sqlite3
import hashlib
import json

# Setup paths
sys.path.insert(0, r"d:\anti\core")
sys.path.insert(0, r"d:\anti")

try:
    from strict_bpm_multi_set_sorter import deep_analyze_track
except ImportError:
    from core.strict_bpm_multi_set_sorter import deep_analyze_track

CACHE_FILE = r"d:\anti\song_analysis_cache.json"
# Rekordbox Master DB Path (Standard location, or from config if available)
# Assuming standard location or D:\anti configuration. 
# In previous turns, it seemed to use pylibrekordbox or local agent logic.
# Let's try to locate the master.db. Usually at %APPDATA%\Pioneer\rekordbox\master.db
# Or D:\master.db based on some contexts? NO, let's look for the standard one.
# But wait, user has "d:\" as workspace. 
# Let's check where `d:\anti\core\rekordbox_mcp\database.py` looks, or just ask the system.
# Actually, I'll search for master.db first or assume standard path.
# Standard Windows: C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox\master.db

DB_PATH = os.path.expandvars(r'C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox\master.db')

TARGET_TITLES = [
    "Take My Breath",
    "Hypnotize",
    "4 SEASONS", 
    "PS118",
    "Gala" # Re-check Gala just in case
]

def get_file_hash(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def find_tracks_in_db():
    print(f"Querying Rekordbox via pyrekordbox...")
    try:
        from pyrekordbox import Rekordbox6Database
        db = Rekordbox6Database(DB_PATH) # Usually it auto-locates but we can pass path? No, standard usage is auto.
        # But if the user provided DB_PATH fails, we might just trust the library default.
        # Let's try standard init.
        db = Rekordbox6Database() # This reads from default location
        
        found_tracks = {}
        
        for kw in TARGET_TITLES:
             # PyRekordbox uses SQLAlchemy style or list comprehension
             # It loads all content? No, it's an object wrapper.
             # We can iterate or filter.
             # content = db.get_content() but that might be huge.
             # Let's use search_content if available or iterate.
             # Or use the raw sqlite connection from it if exposed.
             
             # Actually, Rekordbox6Database decrypts the encryption key. 
             # If I want to use SQL, I need pysqlcipher3.
             # If I assume pyrekordbox works, let's use it.
             
             # Efficient search?
             # db.get_content_of_type('song') ? 
             # Let's just getAll and filter, might be slow but works.
             pass
    except Exception as e:
        print(f"Pyrekordbox init failed: {e}")
        return {}

    all_songs = db.get_content()
    # print(f"Loaded {len(all_songs)} tracks from DB.")
    
    for kw in TARGET_TITLES:
        for song in all_songs:
            if song.Title and kw.lower() in song.Title.lower():
                path = song.FolderPath
                if path and os.path.exists(path):
                    found_tracks[kw] = path
                    print(f"[FOUND] {kw} -> {path}")
                    break
    
    return found_tracks

def analyze_and_update(tracks_map):
    print(f"\nLoading cache from {CACHE_FILE}...")
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except:
        cache = {}
        
    updated = 0
    
    for kw, path in tracks_map.items():
        print(f"Analyzing: {path}")
        try:
            analysis = deep_analyze_track(path)
            if analysis:
                file_hash = get_file_hash(path)
                cache[file_hash] = {
                    "path": path,
                    "analysis": analysis,
                    "hashed_at": 20250122,
                    "source": "rekordbox_lookup"
                }
                updated += 1
                print(f"  [OK] BPM: {analysis.get('bpm')} | Key: {analysis.get('key')}")
            else:
                print("  [Failed] Analysis result empty")
        except Exception as e:
            print(f"  [Error] {e}")
            
    if updated > 0:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print(f"Cache updated with {updated} tracks.")

if __name__ == "__main__":
    found = find_tracks_in_db()
    
    # Check what is still missing
    missing = [kw for kw in TARGET_TITLES if kw not in found]
    if missing:
        print(f"\nStill missing in Rekordbox: {missing}")
        
    if found:
        analyze_and_update(found)
