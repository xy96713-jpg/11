import asyncio
import os
import sys
from pathlib import Path

# Add project paths
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))

from auto_hotcue_generator import generate_hotcues

def verify_physical_consistency():
    print("--- Testing Physical Path Consistency (Force Fallback) ---")
    
    # Mock track data
    file_path = "d:/anti/p2 XG - GALA.mp3"
    bpm = 125.0
    duration = 180.0
    mix_in = 15.5
    mix_out = 160.2
    
    # Generate Hotcues forcing physical path (no content_uuid/id)
    hcs = generate_hotcues(
        audio_file=file_path,
        bpm=bpm,
        duration=duration,
        custom_mix_points={'mix_in': mix_in, 'mix_out': mix_out}
    )
    
    generated_in = hcs['hotcues'].get('B', {}).get('Start')
    generated_out = hcs['hotcues'].get('C', {}).get('Start')
    
    print(f"Advice -> Mix-In: {mix_in}, Mix-Out: {mix_out}")
    print(f"Generated -> Cue B (In): {generated_in}, Cue C (Out): {generated_out}")
    
    # 3. Verification
    # Tolerating small differences due to quantization (beatgrid snapping at 125bpm = 0.48s/beat)
    in_match = abs(generated_in - mix_in) < 0.5
    out_match = abs(generated_out - mix_out) < 0.5
    
    if in_match and out_match:
        print("\n✅ SUCCESS: Physical Hotcues strictly align with Advice!")
    else:
        print("\n❌ FAILURE: Physical Path Mismatch.")
        print(f"  In Diff: {abs(generated_in - mix_in):.3f}s")
        print(f"  Out Diff: {abs(generated_out - mix_out):.3f}s")

if __name__ == "__main__":
    verify_physical_consistency()
