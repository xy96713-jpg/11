import os
import sys
import json
import asyncio
import subprocess
import whisper
import cv2
from rapidocr_onnxruntime import RapidOCR

class FullSpectrumPerceiver:
    def __init__(self, video_path, output_dir):
        self.video_path = video_path
        self.output_dir = output_dir
        self.frames_dir = os.path.join(output_dir, "frames_v6")
        self.audio_path = os.path.join(output_dir, "temp_audio.wav")
        os.makedirs(self.frames_dir, exist_ok=True)
        
        # Initialize Engines
        print("[*] Initializing Engines (Whisper & RapidOCR)...", file=sys.stderr)
        self.ocr_engine = RapidOCR()
        self.whisper_model = whisper.load_model("base") # Use 'base' for better Chinese support than 'tiny'

    def extract_audio(self):
        print("[*] Extracting Audio for ASR...", file=sys.stderr)
        cmd = [
            "ffmpeg", "-y",
            "-i", self.video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            self.audio_path
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"[!] FFmpeg Audio Error: {e.stderr}", file=sys.stderr)
            raise

    def transcribe_audio(self):
        print("[*] Running ASR (Whisper: Every Word)...", file=sys.stderr)
        result = self.whisper_model.transcribe(self.audio_path, language="zh", verbose=False)
        return result.get("segments", [])

    def adaptive_sampling(self, threshold=0.3):
        """Use FFmpeg to detect scenes/changes for better frame coverage."""
        print("[*] Performing Adaptive Visual Sampling...", file=sys.stderr)
        # We'll use a mix of fixed interval (10s) and scene detection if possible,
        # but for speed and simplicity, we'll start with 5s intervals mapping to OCR.
        # Professional version: Extract keyframes where 'scene' change > threshold
        cmd = [
            "ffmpeg", "-y",
            "-i", self.video_path,
            "-vf", f"select='gt(scene,{threshold})+eq(n,0)',showinfo",
            "-vsync", "vfr",
            os.path.join(self.frames_dir, "key_%03d.jpg")
        ]
        # Since scene detection might yield too many or too few, we fallback to 5s grid if needed.
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Collect generated frames
        frames = sorted([f for f in os.listdir(self.frames_dir) if f.startswith("key_")])
        if len(frames) < 3: # Fallback to grid
             print("[!] Scene detection limited. Using 5s grid fallback.", file=sys.stderr)
             cmd_fallback = [
                 "ffmpeg", "-y",
                 "-i", self.video_path,
                 "-vf", "fps=1/5",
                 os.path.join(self.frames_dir, "grid_%03d.jpg")
             ]
             subprocess.run(cmd_fallback, check=True, capture_output=True)
             frames = sorted([f for f in os.listdir(self.frames_dir)])
        
        return frames

    def perform_ocr_on_frames(self, frame_files):
        print("[*] Running Local OCR (RapidOCR: Every Subtitle)...", file=sys.stderr)
        ocr_results = []
        for f in frame_files:
            img_path = os.path.join(self.frames_dir, f)
            img = cv2.imread(img_path)
            
            # Subtitle optimization: Focus on bottom 25% of the frame
            h, w = img.shape[:2]
            bottom_crop = img[int(h*0.7):h, 0:w]
            
            result, _ = self.ocr_engine(bottom_crop)
            if result:
                text_content = " ".join([line[1] for line in result])
                ocr_results.append({
                    "frame": f,
                    "text": text_content
                })
        return ocr_results

    async def run(self):
        # 1. ASR
        if not os.path.exists(self.audio_path):
            self.extract_audio()
        asr_segments = self.transcribe_audio()

        # 2. Visual Sampling
        frame_files = self.adaptive_sampling()

        # 3. OCR
        ocr_data = self.perform_ocr_on_frames(frame_files)

        # 4. Fusion
        final_truth = {
            "asr_transcript": asr_segments,
            "ocr_subtitles": ocr_data,
            "video_file": os.path.basename(self.video_path)
        }
        
        output_file = os.path.join(self.output_dir, "full_spectrum_truth.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_truth, f, ensure_ascii=False, indent=2)
        
        print(f"[+] Full Spectrum Perception Success: {output_file}", file=sys.stderr)
        return output_file

if __name__ == "__main__":
    v_path = sys.argv[1]
    out_dir = sys.argv[2]
    perceiver = FullSpectrumPerceiver(v_path, out_dir)
    asyncio.run(perceiver.run())
