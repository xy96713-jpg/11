import os
import sys
import argparse
import time
import torch
import warnings
from pathlib import Path

# Filter warnings for cleaner output
warnings.filterwarnings("ignore")

def print_step(step, msg):
    print(f"[{step}] \033[96m{msg}\033[0m")

def print_error(msg):
    print(f"\033[91m[ERROR] {msg}\033[0m")

def check_dependencies():
    try:
        import faster_whisper
        import soundfile
    except ImportError as e:
        print_error(f"Missing dependency: {e.name}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def separate_vocals(audio_path, output_dir):
    """
    Uses Demucs to separate vocals.
    Returns path to isolated vocals.wav.
    """
    print_step("DEMUCS", f"Separating vocals for: {audio_path.name}...")
    
    # Check if demucs is installed
    try:
        import demucs.separate
    except ImportError:
        print_error("Demucs not installed. Skipping separation (results may incur hallucinations).")
        return audio_path

    # Run Demucs (lightweight model htdemucs, cpu optimized if needed)
    # Using CLI wrapper via os.system might be safer for environment isolation, 
    # but library call gives specific paths. Let's try subprocess.
    import subprocess
    
    cmd = [
        sys.executable, "-m", "demucs.separate",
        "-n", "htdemucs", # High quality, faster hybrid transformer
        "--two-stems", "vocals", # Only need vocals
        str(audio_path),
        "-o", str(output_dir)
    ]
    
    # Only use basic print for subprocess 
    print(f"Executing Demucs: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error("Demucs failed:")
        print(result.stderr)
        return audio_path # Fallback to original
    
    # Locate processed file: output_dir/htdemucs/song_name/vocals.wav
    # Demucs output structure is standard
    song_name = audio_path.stem
    vocals_path = output_dir / "htdemucs" / song_name / "vocals.wav"
    
    if vocals_path.exists():
        print_step("DEMUCS", "Vocals isolated successfully.")
        return vocals_path
    else:
        print_error(f"Could not find separated vocals at expected path: {vocals_path}")
        return audio_path

def format_timestamp(seconds):
    """
    Converts seconds to [mm:ss.xx] format for LRC.
    """
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    # LRC standard aims for hundredths (xx), so .2f works
    return f"[{minutes:02d}:{remaining_seconds:05.2f}]"

def generate_lrc(segments, output_file):
    print_step("EXPORT", f"Writing LRC to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("[by:Antigravity Skill 10]\n")
        f.write(f"[app:Faster-Whisper]\n")
        
        for segment in segments:
            # Segment level timestamp
            start_time = segment.start
            text = segment.text.strip()
            
            # Skip empty lines
            if not text:
                continue
                
            timestamp = format_timestamp(start_time)
            f.write(f"{timestamp}{text}\n")
            # print(f"{timestamp}{text}") # Verbose preview

def main():
    parser = argparse.ArgumentParser(description="Skill 10: Automatic Lyrics/Subtitle Generator")
    parser.add_argument("input_file", help="Path to input audio/video file")
    parser.add_argument("--mode", choices=['speech', 'song'], default='song', help="Processing mode (song enables vocal separation)")
    parser.add_argument("--model", default="medium", help="Whisper model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--device", default="auto", help="Device to use (cuda, cpu, auto)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print_error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    check_dependencies()
    from faster_whisper import WhisperModel
    
    # 1. Device Selection
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    compute_type = "float16" if device == "cuda" else "int8"
    print_step("INIT", f"Loading Whisper ({args.model}) on {device} ({compute_type})...")
    
    try:
        model = WhisperModel(args.model, device=device, compute_type=compute_type)
    except Exception as e:
        print_error(f"Model load failed: {e}")
        print("Fallback to int8 cpu...")
        model = WhisperModel(args.model, device="cpu", compute_type="int8")

    # 2. Vocal Separation (if Song mode)
    process_path = input_path
    temp_dir = Path("d:/anti/temp/skill10_separation") # Use absolute temp path
    
    if args.mode == 'song':
        process_path = separate_vocals(input_path, temp_dir)
        
    # 3. Transcription
    print_step("WHISPER", f"Transcribing {process_path.name}...")
    
    segments, info = model.transcribe(
        str(process_path), 
        beam_size=5, 
        vad_filter=True, # Critical for songs to ignore instrumental breaks
        word_timestamps=False # LRC mainly needs Line timestamps, word is for karaoke (complex)
    )
    
    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
    
    # 4. Generate Output (Wait for generator)
    lrc_path = input_path.with_suffix(".lrc")
    
    # Convert generator to list to force execution and show progress
    segments_list = []
    start_time = time.time()
    
    for i, segment in enumerate(segments):
        segments_list.append(segment)
        # Simple progress indicator
        if i % 10 == 0:
            sys.stdout.write(f"\rProcessed {segment.end:.1f}s...")
            sys.stdout.flush()
            
    print(f"\nTranscription complete in {time.time() - start_time:.2f}s")
    
    # 5. Export
    generate_lrc(segments_list, lrc_path)
    
    print_step("DONE", f"Lyrics saved to: {lrc_path}")

if __name__ == "__main__":
    main()
