import json
import os
import sys
from pathlib import Path

# Path setup
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from core.mastering_core import MasteringAnalyzer

def run_diagnostic():
    print("🚀 [SOTA 2026 Diagnostic] Starting self-test...")
    analyzer = MasteringAnalyzer()
    
    # We'll use a dummy call to verify dimensions map
    print("🧬 [SOTA 2026] Checking Dimension Map...")
    dummy_dna = analyzer.extract_sonic_dna("non_existent_file.mp3")
    
    # Actually, let's just check the class's dimension_map if we can, 
    # but it's local to the method. Let's just run it on a valid file.
    
    # Find a valid file from cache for real testing
    cache_path = r"d:\anti\scripts\song_analysis_cache.json"
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    test_file = None
    for key, data in cache.items():
        fpath = data.get('file_path')
        if fpath and os.path.exists(fpath):
            test_file = fpath
            break
            
    if not test_file:
        print("❌ No valid test file found.")
        return

    print(f"🎬 [SOTA 2026] Running analysis on: {os.path.basename(test_file)}")
    report = analyzer.extract_sonic_dna(test_file)
    
    if "cognitive_dna" in report:
        print("✅ [SUCCESS] Cognitive DNA dimension is ACTIVE.")
        print(f"📡 [Hits] {report['cognitive_dna']}")
    else:
        print("❌ [FAILURE] Cognitive DNA dimension is MISSING.")

    # Check for 2026 Spatial tags
    spatial = report.get('spatial', [])
    sota_tags = ["3D Source Separation", "Acoustic Pinpointing", "Edge-diffraction Modeling"]
    found_sota = [t['tag'] for t in spatial if t['tag'] in sota_tags]
    if found_sota:
        print(f"✅ [SUCCESS] 2026 Spatial Hearing tags detected: {found_sota}")
    else:
        print("ℹ️ [Info] No 2026 Spatial tags triggered for this specific track (Expected).")

if __name__ == "__main__":
    run_diagnostic()
