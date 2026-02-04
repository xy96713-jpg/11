
import json
from pathlib import Path

cache_file = Path(r"d:/anti/scripts/song_analysis_cache.json")
if not cache_file.exists():
    print("Cache file not found.")
    exit(1)

with open(cache_file, 'r', encoding='utf-8') as f:
    cache = json.load(f)

fields_to_check = ['energy', 'bpm', 'key', 'duration']
stats = {f: 0 for f in fields_to_check}
none_tracks = {f: [] for f in fields_to_check}

for file_path, data in cache.items():
    analysis = data.get('analysis', {})
    for field in fields_to_check:
        if analysis.get(field) is None:
            stats[field] += 1
            if len(none_tracks[field]) < 5:
                none_tracks[field].append(f"{data.get('artist')} - {Path(file_path).stem}")

print(f"Total tracks in cache: {len(cache)}")
for field in fields_to_check:
    print(f"Tracks with None {field}: {stats[field]}")
    if none_tracks[field]:
        print(f"  Examples: {', '.join(none_tracks[field])}")
