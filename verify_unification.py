
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path("d:/anti")))

print("🧪 System-Wide Unification Audit...")

# 1. Test core.cache_manager
try:
    from core.cache_manager import load_cache, DEFAULT_CACHE_PATH
    print(f"✅ core.cache_manager points to: {DEFAULT_CACHE_PATH}")
    cache = load_cache()
    print(f"✅ Global Cache loaded. Entries: {len(cache)}")
except Exception as e:
    print(f"❌ core.cache_manager issue: {e}")

# 2. Test Set Sorter Integration
try:
    # We add the skills folder to path to mock its import environment
    sys.path.insert(0, str(Path("d:/anti/skills/set_curation_expert")))
    import enhanced_harmonic_set_sorter as sorter
    print(f"✅ Sorter CACHE_FILE: {sorter.CACHE_FILE}")
    
    if str(sorter.CACHE_FILE).lower().replace('\\', '/') == "d:/anti/scripts/song_analysis_cache.json":
        print("🎯 UNIFICATION SUCCESS: Sorter is aligned with Global Scripts Cache.")
    else:
        print(f"⚠️ UNIFICATION PARTIAL: Sorter is using {sorter.CACHE_FILE}")
except Exception as e:
    print(f"❌ Sorter integration issue: {e}")

# 3. Data Integrity Check (The 101st Dimension)
ninja_hash = "fba8c1a7770e28f3a8b4b1a1" # Partial or dummy for test
# Let's find Ninja in the actual cache
found_ninja = False
for k, v in cache.items():
    if "7981" in str(v.get('file_path', '')) or "Ninja" in str(v.get('file_path', '')):
        dna = v.get('analysis', {}).get('sonic_dna')
        if dna:
            print(f"🧬 DATA SUCCESS: Track '{v.get('file_path')}' has Sonic DNA: {dna}")
            found_ninja = True
            break

if not found_ninja:
    print("❓ Ninja track not found or missing Sonic DNA in unified cache.")

print("\n🏁 Audit Complete.")
