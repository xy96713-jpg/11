import os
import sys
import json
import torch
from faster_whisper import WhisperModel
import subprocess
from audio_separator.separator import Separator

class SubtitleEngineV3:
    def __init__(self, model_size="large-v3", device="cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        print(f"[*] Initializing Subtitle Engine 3.0 on {self.device}...")
        self.model = WhisperModel(model_size, device=self.device, compute_type=self.compute_type)
        
        # Load Lyric Context
        try:
            with open("lyrics_context.json", "r", encoding="utf-8") as f:
                self.LYRIC_CONTEXT = json.load(f)
        except Exception as e:
            print(f"[!] Warning: Could not load lyrics_context.json: {e}")
            self.LYRIC_CONTEXT = {}

    def separate_vocals_mdx(self, audio_path):
        """Use UVR MDX-Net for extreme isolation."""
        print("[*] Performing MDX-Net Separation (UVR-MDX-NET-Voc-FT)...")
        separator = Separator()
        separator.load_model('UVR-MDX-NET-Voc-FT.onnx')
        
        # This will save extracted files in the same directory by default
        output_files = separator.separate(audio_path)
        
        # MDX-Net usually outputs '(Vocals)_...' and '(Instrumental)_...'
        vocals_path = ""
        for file in output_files:
            if "Vocals" in file:
                vocals_path = file
                break
        
        if not vocals_path:
            raise Exception("Vocal separation failed: Vocals file not found.")
            
        return vocals_path

    def transcribe_with_context(self, audio_path, song_keys=None):
        """Transcribe with Lyric Fingerprint injection."""
        prompt = "这是一段混音歌曲的人声，请准确记录歌词。"
        if song_keys:
            # Skill 06 Logic: Inject known lyrics to guide the AI
            relevant_lyrics = " ".join([self.LYRIC_CONTEXT.get(k, "") for k in song_keys])
            prompt += f" 包含以下歌词背景: {relevant_lyrics}"
            print(f"[*] Injecting context for: {', '.join(song_keys)}")

        print("[*] Transcribing with Mastermind Logic...")
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            word_timestamps=True,
            initial_prompt=prompt
        )

        srt_items = []
        for i, segment in enumerate(segments):
            # Filtering for pure clarity
            if segment.avg_logprob < -0.8:
                continue
                
            srt_items.append({
                "index": i + 1,
                "start": self.format_timestamp(segment.start),
                "end": self.format_timestamp(segment.end),
                "text": segment.text.strip()
            })
        
        return srt_items

    def format_timestamp(self, seconds):
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
        print(f"[+] 3.0 SRT exported to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lyric_engine.py <audio_path> [--songs XG_HYPNOTIZE,NewJeans_Super_Shy]")
        sys.exit(1)

    input_file = sys.argv[1]
    song_keys = None
    if "--songs" in sys.argv:
        idx = sys.argv.index("--songs")
        song_keys = sys.argv[idx+1].split(",")

    engine = SubtitleEngineV3()
    vocal_track = engine.separate_vocals_mdx(input_file)
    results = engine.transcribe_with_context(vocal_track, song_keys)
    
    output_srt = os.path.splitext(input_file)[0] + "_3.0.srt"
    engine.export_srt(results, output_srt)
