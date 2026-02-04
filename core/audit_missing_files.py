import json
import os

cache_path = r"d:\anti\scripts\song_analysis_cache.json"
with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

missing_on_disk = []
for key, data in cache.items():
    fpath = data.get('file_path')
    if fpath and not os.path.exists(fpath):
        missing_on_disk.append(fpath)

print(f"Total entries: {len(cache)}")
print(f"Missing on disk: {len(missing_on_disk)}")
for m in missing_on_disk[:10]:
    print(f" - {m}")
