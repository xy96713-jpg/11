import asyncio
import os
import sys
from pathlib import Path

# Add project paths
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))

from enhanced_harmonic_set_sorter import create_enhanced_harmonic_sets
from auto_hotcue_generator import generate_hotcues

async def verify_cue_consistency():
    playlist = "Boiler Room"
    print(f"--- Testing Playlist: {playlist} ---")
    
    # 1. Get Set with Advice
    sets = await create_enhanced_harmonic_sets(playlist_name=playlist, is_master=True)
    if not sets or not sets[0]:
        print("No tracks found in playlist.")
        return
    
    # Pick a track that has recommended points
    suitable_track = None
    for track in sets[0]:
        if track.get('mix_in_point') and track.get('mix_out_point'):
            suitable_track = track
            break
    
    if not suitable_track:
        suitable_track = sets[0][1]

    title = suitable_track.get('title', 'Unknown')
    mix_in = suitable_track.get('mix_in_point')
    mix_out = suitable_track.get('mix_out_point')
    file_path = suitable_track.get('file_path')
    content_uuid = suitable_track.get('content_uuid')
    
    print(f"\nTrack: {title}")
    print(f"Advice -> Mix-In: {mix_in}, Mix-Out: {mix_out}")
    print(f"Content UUID: {content_uuid}")
    
    # 2. Generate Hotcues using these points
    hcs = generate_hotcues(
        audio_file=file_path,
        bpm=suitable_track.get('bpm'),
        duration=suitable_track.get('duration'),
        content_uuid=content_uuid,
        custom_mix_points={'mix_in': mix_in, 'mix_out': mix_out}
    )
    
    generated_in = hcs['hotcues'].get('B', {}).get('Start')
    generated_out = hcs['hotcues'].get('C', {}).get('Start')
    
    print(f"Generated -> Cue B (In): {generated_in}, Cue C (Out): {generated_out}")
    
    # 3. Verification
    # Tolerating small differences due to quantization (beatgrid snapping)
    in_match = abs(generated_in - (mix_in or 0)) < 0.5 if mix_in else True
    out_match = abs(generated_out - (mix_out or 0)) < 0.5 if mix_out else True
    
    if in_match and out_match:
        print("\n✅ SUCCESS: Hotcues strictly align with Advice!")
    else:
        print("\n❌ FAILURE: Mismatch detected between Advice and Hotcues.")
        if not in_match: print(f"  In Diff: {abs(generated_in - (mix_in or 0)):.3f}s")
        if not out_match: print(f"  Out Diff: {abs(generated_out - (mix_out or 0)):.3f}s")

if __name__ == "__main__":
    asyncio.run(verify_cue_consistency())
