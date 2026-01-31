import os
import sys
from pathlib import Path
import json

# Add project root to sys.path
sys.path.insert(0, r"D:\anti")
sys.path.insert(0, r"D:\anti\core")
sys.path.insert(0, r"D:\anti\skills")
sys.path.insert(0, r"D:\anti\exporters")

from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format
from exporters.xml_exporter import export_to_rekordbox_xml

def test_pro_dj_pipeline():
    # Use a track that we know exists
    track_path = r"D:\song\Aaliyah - Old School.mp3"
    if not os.path.exists(track_path):
        print(f"Track not found: {track_path}")
        return

    print(f"--- Testing Pro DJ Pipeline for: {os.path.basename(track_path)} ---")
    
    # 1. Simulate Analysis results (or run real analysis if possible)
    # Using real analysis via auto_hotcue_generator
    try:
        from core.enhanced_structure_detector import detect_structure_enhanced
        print("Running AI Structure Detection...")
        structure = detect_structure_enhanced(track_path)
        print(f"Detected Structure: {json.dumps(structure.get('structure'), indent=2)}")
        
        # 2. Generate Pro HotCues (with quantization)
        print("\nGenerating Pro Quantized Cues...")
        bpm = 120.0 # Standard fallback or detected
        raw_cues = generate_hotcues(track_path, bpm=bpm, structure=structure)
        
        print("\nGenerated Cues (Internal):")
        for k, v in raw_cues.items():
            if isinstance(v, dict):
                print(f"  {k}: {v.get('seconds')}s - {v.get('name')}")
        
        # 3. Format for Rekordbox
        rb_cues = hotcues_to_rekordbox_format(raw_cues)
        
        # 4. Export to XML
        output_xml = Path(r"D:\anti\AI_PRO_DJ_TEST.xml")
        track_data = [{
            'file_path': track_path,
            'track_info': {'title': 'Snooze (AI Pro Test)', 'artist': 'SZA'},
            'analysis': {
                'bpm': raw_cues.get('bpm', 120),
                'duration': 200, # Mock
                'key': '11A'
            },
            'pro_hotcues': rb_cues
        }]
        
        print(f"\nExporting to {output_xml}...")
        export_to_rekordbox_xml(track_data, output_xml, playlist_name="!! AI BRAIN DJ TEST !!")
        print("Export successful!")
        
        # 5. Verify XML content
        with open(output_xml, 'r', encoding='utf-8') as f:
            content = f.read()
            passed = True
            
            print("\nVerification Results:")
            if 'POSITION_MARK' in content:
                print("  [OK] Found POSITION_MARK tags.")
            else:
                print("  [FAIL] Missing POSITION_MARK tags.")
                passed = False
                
            if 'Num="-1"' in content:
                print("  [OK] Found Memory Cues (Num=-1).")
            else:
                print("  [FAIL] Missing Memory Cues.")
                passed = False
                
            if 'MIX:' in content:
                print("  [OK] Found Mix Type identification label.")
            else:
                print("  [FAIL] Missing Mix Type label.")
                passed = False
                
            if 'Num="7"' in content or 'H: [Loop]' in content:
                print("  [OK] Found HotCue H (Emergency Loop).")
            else:
                print("  [FAIL] Missing HotCue H.")
                passed = False
                
            if passed:
                print("\nVERIFICATION PASSED: Brain DJ Enterprise features detected.")
            else:
                print("\nVERIFICATION FAILED: Missing elite cueing components.")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pro_dj_pipeline()
