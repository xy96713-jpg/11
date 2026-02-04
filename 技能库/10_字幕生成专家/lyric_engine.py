import os
import sys
import torch
from faster_whisper import WhisperModel
import subprocess

class SubtitleEngine:
    def __init__(self, model_size="large-v3", device="cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        print(f"[*] Initializing Subtitle Engine on {self.device}...")
        self.model = WhisperModel(model_size, device=self.device, compute_type=self.compute_type)

    def separate_vocals(self, audio_path):
        """Use Demucs to isolate vocals from mixed tracks."""
        print("[*] Separating vocals using Demucs...")
        output_dir = "temp_sep"
        # Standard DJ mandate: separate vocals, discard everything else
        cmd = ["demucs", "--two-stems=vocals", "-o", output_dir, audio_path]
        subprocess.run(cmd, check=True)
        
        # Construct path to separated vocals
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        vocals_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
        return vocals_path

    def transcribe(self, audio_path, overlap_threshold=0.85):
        """Transcribe audio with overlap filtering."""
        print("[*] Transcribing...")
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            word_timestamps=True,
            initial_prompt="这是一段混音歌曲的人声，请准确记录歌词。对于人声重叠模糊的部分请留白。"
        )

        srt_items = []
        for i, segment in enumerate(segments):
            # DJ LOGIC: Filter by confidence (probability)
            # If avg_logprob is too low, it's likely overlapping or noise
            if segment.avg_logprob < -1.0 or segment.no_speech_prob > 0.6:
                print(f"[!] Low confidence segment at {segment.start:.2f}s, skipping to avoid hallucinations.")
                continue
                
            # SRT format: [index, start, end, text]
            srt_items.append({
                "index": i + 1,
                "start": self.format_timestamp(segment.start),
                "end": self.format_timestamp(segment.end),
                "text": segment.text.strip()
            })
        
        return srt_items

    def format_timestamp(self, seconds):
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def export_srt(self, items, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(f"{item['index']}\n")
                f.write(f"{item['start']} --> {item['end']}\n")
                f.write(f"{item['text']}\n\n")
        print(f"[+] SRT exported to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lyric_engine.py <audio_path>")
        sys.exit(1)

    input_file = sys.argv[1]
    engine = SubtitleEngine()
    
    # Check if it's a song (DJ input is usually songs)
    vocal_track = engine.separate_vocals(input_file)
    results = engine.transcribe(vocal_track)
    
    output_srt = os.path.splitext(input_file)[0] + ".srt"
    engine.export_srt(results, output_srt)
