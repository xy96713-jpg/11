import json
import os

cache_path = r"d:\anti\scripts\song_analysis_cache.json"
with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

for key, data in cache.items():
    analysis = data.get('analysis', {})
    if 'god_mode_details' not in analysis:
        fpath = data.get('file_path')
        print(f"MISSING: {key}")
        print(f"PATH: {fpath}")
