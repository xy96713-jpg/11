import json
import os
from pathlib import Path

CACHE_PATH = r"d:\anti\scripts\song_analysis_cache.json"

if not os.path.exists(CACHE_PATH):
    print(f"❌ Cache missing at {CACHE_PATH}")
    exit(1)

with open(CACHE_PATH, 'r', encoding='utf-8') as f:
    cache = json.load(f)

total = len(cache)
has_sonic = 0
missing_sonic = 0
path_missing = 0
invalid_path_format = 0

for k, v in cache.items():
    if not isinstance(v, dict): continue
    
    analysis = v.get('analysis', {})
    if 'sonic_dna' in analysis and analysis['sonic_dna']:
        has_sonic += 1
    else:
        missing_sonic += 1
        fp = v.get('file_path')
        if not fp:
            path_missing += 1
        else:
            if not os.path.exists(fp):
                path_missing += 1
                if "file://" in fp or fp.startswith("/"):
                    invalid_path_format += 1

print(f"Total entries: {total}")
print(f"Has Sonic DNA: {has_sonic}")
print(f"Missing Sonic DNA: {missing_sonic}")
print(f"Invalid/Missing paths (for missing sonic): {path_missing}")
print(f"Likely incorrect path format: {invalid_path_format}")

# Sample one missing sonic
for k, v in cache.items():
    analysis = v.get('analysis', {})
    if 'sonic_dna' not in analysis:
        print(f"\nSample target for enrichment:")
        print(f"  Key: {k}")
        print(f"  Path: {v.get('file_path')}")
        break
