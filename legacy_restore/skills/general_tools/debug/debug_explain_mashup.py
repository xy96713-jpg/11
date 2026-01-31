import json
from pathlib import Path

cache_path = Path(r"d:\anti\song_analysis_cache.json")

def find_track(query):
    if not cache_path.exists():
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    for k, v in cache.items():
        fp = v.get('file_path', '')
        if query.lower() in fp.lower():
            print(json.dumps(v, indent=2, ensure_ascii=False))
            break

if __name__ == "__main__":
    find_track("Straight Up")
