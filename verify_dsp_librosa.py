
import os
import sys
import asyncio
from pathlib import Path

# Fix paths
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core")

async def verify():
    print("🧪 Verifying V30.1 DSP Engine (Librosa + YAMNet)...")
    
    # 1. Import AudioCortex
    try:
        from core.audio_cortex import cortex
        print("✅ Core Module Imported.")
    except ImportError as e:
        print(f"❌ Import Failed: {e}")
        return

    # 2. Find a test file
    # We'll search for a known file or just pick one commonly found
    # Let's try to find a wav or mp3
    test_file = None
    search_dirs = ["D:/Music", "D:/Downloads", "D:/Songs"] # Hypothesized paths
    # Better: Use the 'find_by_name' tool equivalent logic or just hardcode if we knew one.
    # We will try to scan current dir or a known skills asset.
    # Let's check d:/anti/skills first
    
    import glob
    candidates = glob.glob("d:/anti/**/*.mp3", recursive=True) + glob.glob("d:/anti/**/*.wav", recursive=True)
    
    if not candidates:
        print("⚠️ No local audio files found in d:/anti for testing.")
        print("Please assume engine load is compliant if no crash.")
        # Try a dummy path to trigger the load at least
        test_file = "d:/anti/dummy_test.mp3"
    else:
        test_file = candidates[0]
        print(f"📂 Test File: {test_file}")

    # 3. Trigger Analysis
    print("🧠 Invoking Cortex...")
    # This will trigger lazy load of librosa/tf
    if os.path.exists(test_file):
        result = cortex.analyze_track(test_file, force_refresh=True)
        print(f"🎉 Result: {result}")
    else:
        # Trigger init only
        cortex._init_dsp_engine()
        print(f"✅ Engine Init Check: {cortex.dsp_engine}")

if __name__ == "__main__":
    asyncio.run(verify())
