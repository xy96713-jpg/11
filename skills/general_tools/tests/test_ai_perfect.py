from pyrekordbox.rbxml import RekordboxXml, encode_path
import os
import shutil
import json
from pathlib import Path

def generate_perfect_xml():
    print("=== AI Perfect XML Generator (Using pyrekordbox) ===")
    
    # 1. Setup paths
    output_dir = "D:/生成的set/perfect_test"
    os.makedirs(output_dir, exist_ok=True)
    out_xml = "D:/生成的set/AI_PERFECT_PROOF.xml"
    
    # 2. Pick a source song
    source_path = "D:/song/kpop/NewJeans - OMG (BRLLNT Remix) [1416029752].mp3"
    if not os.path.exists(source_path):
        print(f"Error: Source not found {source_path}")
        return

    # Create a fresh copy to force Rekordbox to treat it as a new track
    test_filename = "AI_PERFECT_SONG.mp3"
    test_path = os.path.join(output_dir, test_filename).replace('\\', '/')
    shutil.copy2(source_path, test_path)
    print(f"Created test file: {test_path}")

    # 3. Build XML using pyrekordbox
    # Initialize empty XML
    xml = RekordboxXml(name="rekordbox", version="6.0.0", company="Pioneer DJ")
    
    # Use real analysis data if available, or fake it for the proof
    # Let's just use hardcoded points for the proof to be certain
    bpm = 125.0
    duration = 200.0
    
    # Add track
    # Note: encode_path handles the file://localhost/... conversion correctly
    track = xml.add_track(test_path)
    track.set("Name", "!! AI PERFECT PROOF !!")
    track.set("Artist", "Antigravity AI")
    track.set("Kind", "Music File")
    track.set("AverageBpm", bpm)
    track.set("TotalTime", int(duration))
    track.set("Tonality", "11B")
    
    # Add BeatGrid (Tempo)
    track.add_tempo(Inizio=0.0, Bpm=bpm, Metro="4/4", Battito=1)
    
    # Add HotCues
    # A=0, B=1, C=2, D=3, E=4
    track.add_mark(Name="!! AI_ENTRY_A !!", Type="cue", Start=10.0, Num=0)
    track.add_mark(Name="!! AI_TRANS_B !!", Type="cue", Start=25.0, Num=1)
    track.add_mark(Name="!! AI_EXIT_C !!", Type="cue", Start=160.0, Num=2)
    track.add_mark(Name="!! AI_END_D !!", Type="cue", Start=180.0, Num=3)
    track.add_mark(Name="!! AI_DROP_E !!", Type="cue", Start=45.0, Num=4)
    
    # Add Memory Cue
    track.add_mark(Name="!! AI_MEM !!", Type="cue", Start=10.0, Num=-1)

    # Add Playlist
    pl = xml.add_playlist("!!! AI_PERFECT_PLAYLIST !!!")
    pl.add_track(track.TrackID)
    
    # Save
    xml.save(out_xml)
    print(f"[SUCCESS] Perfect XML saved to: {out_xml}")
    print("This XML was generated using the official pyrekordbox library's internal logic.")

if __name__ == "__main__":
    generate_perfect_xml()
