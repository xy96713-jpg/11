from pyrekordbox import anlz
import os
import numpy as np

def test_anlz_reading():
    # Pick a recently analyzed file (e.g. from the list earlier)
    # The one ending in bba4 was analyzed 2026/1/19
    anlz_path = r"C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\USBANLZ\008\e5d59-f6a2-41a7-9102-f6750126bba4\ANLZ0000.EXT"
    if not os.path.exists(anlz_path):
        # Fallback to the other one if needed
        anlz_path = r"C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\USBANLZ\001\25081-bf23-4bfc-a7ba-4c896663cfe8\ANLZ0000.EXT"
        
    print(f"Reading {anlz_path}...")
    try:
        ext = anlz.AnlzFile.parse_file(anlz_path)
        print(f"Tags found: {ext.tag_types}")
            
        # Try Beatgrid (PQT2 - NXS2 Format)
        if "PQT2" in ext:
            print("\nBeatgrid (PQT2) Analysis:")
            pqtz = ext.get_tag("PQT2")
            # get() returns (beats, bpms, times)
            beats, bpms, times = pqtz.get()
            print(f" Found {len(beats)} beats.")
            for i in range(min(5, len(beats))):
                print(f"  Beat {beats[i]}: {times[i]:.3f}s (BPM: {bpms[i]:.2f})")
        
        # Try Song Structure (PSSI)
        if "PSSI" in ext:
            print("\nSong Structure (PSSI):")
            pssi = ext.get_tag("PSSI")
            structure = pssi.get()
            # print(structure) # Usually Container
            # Iterate through sections
            if hasattr(structure, 'entries'):
                for entry in structure.entries:
                    # entry usually has beat_no, kind_id
                    print(f"  Segment: {entry}")
            else:
                print(f"  Structure data: {structure}")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_anlz_reading()
