import os
import sys
import json
import torch
from faster_whisper import WhisperModel
import subprocess
from audio_separator.separator import Separator
from difflib import SequenceMatcher
import numpy as np
import librosa

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
        vocals_path = f"{os.path.splitext(audio_path)[0]}_(Vocals)_UVR-MDX-NET-Voc_FT.wav"
        if os.path.exists(vocals_path):
            print(f"[*] Reusing existing vocals file: {vocals_path}")
            return vocals_path
            
        print("[*] Performing MDX-Net Separation (UVR-MDX-NET-Voc_FT)...")
        separator = Separator()
        separator.load_model('UVR-MDX-NET-Voc_FT.onnx')
        
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

    def transcribe_with_context(self, audio_path, song_keys=None, language=None):
        """Transcribe with Lyric Fingerprint injection and granular segmentation."""
        prompt = "这是一段混音歌曲的人声，请按歌词分行记录，确保时间轴精确。"
        if song_keys:
            # Flatten the list of lyrics for the initial prompt
            lyrics_list = []
            for k in song_keys:
                lines = self.LYRIC_CONTEXT.get(k, [])
                if isinstance(lines, list):
                    lyrics_list.extend(lines)
                else:
                    lyrics_list.append(lines)
            relevant_lyrics = " ".join(lyrics_list)
            # FORCE Hangul hints for Whisper
            relevant_lyrics += " [떨리는 지금도, 누구보다도, 나 원래 말도 잘하고]"
            prompt += f" 包含以下歌词背景: {relevant_lyrics}"
            print(f"[*] Injecting context with Hangul Anchors for: {', '.join(song_keys)}")

        print(f"[*] Transcribing with Mastermind Studio Logic (Full VAD Mode)...")
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            word_timestamps=True,
            initial_prompt=prompt,
            language=language,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.15, # Max sensitivity for faint vocals
                min_speech_duration_ms=100,
                max_speech_duration_s=7,
                min_silence_duration_ms=150, # Capture even short gaps/breaths
                speech_pad_ms=100 # Add padding to avoid clipping
            )
        )

        # 5.3 Mastermind Semantic Alignment (Fixed Consumption)
        srt_items = []
        all_words = []
        for segment in segments:
            if segment.avg_logprob < -3.0: continue
            if segment.words:
                for w in segment.words:
                    # Basic dedup
                    if all_words and w.word.strip().lower() == all_words[-1].word.strip().lower():
                        if abs(w.start - all_words[-1].start) < 0.2:
                            continue
                    all_words.append(w)

        # Semantic Reconstruction 5.3
        if all_words:
            print(f"[*] Starting 5.3 Ultimate Semantic Reconstruction for {len(all_words)} words...")
            i = 0
            while i < len(all_words):
                best_match_len = 0
                best_line_text = ""
                best_tag = ""
                
                # Look ahead window (max 15 words)
                for window_size in range(1, 16):
                    if i + window_size > len(all_words): break
                    
                    candidate_words = all_words[i:i+window_size]
                    candidate_text = " ".join([w.word.strip() for w in candidate_words])
                    
                    # Check against official lyrics
                    for tag, lines in self.LYRIC_CONTEXT.items():
                        for line in lines:
                            match_threshold = 0.35 if "NewJeans" in tag else 0.50
                            if SequenceMatcher(None, candidate_text.lower(), line.lower()).ratio() > match_threshold:
                                # We found a strong official match
                                if window_size > best_match_len:
                                    best_match_len = window_size
                                    best_line_text = line
                                    best_tag = tag.replace("_", " ")

                if best_match_len > 0:
                    # OFFICIAL MATCH FOUND: Consume the words and export as one block
                    start_val = all_words[i].start
                    end_val = all_words[i + best_match_len - 1].end
                    
                    # Display text without song tag
                    display_text = self.filter_profanity(best_line_text)
                    
                    srt_items.append({
                        "start_raw": start_val,
                        "end_raw": end_val,
                        "text": display_text
                    })
                    
                    i += best_match_len # CONSUME
                else:
                    # NO MATCH: Use traditional splitting for this segment
                    # Group words until a significant gap or too long
                    chunk = []
                    chunk_start = all_words[i].start
                    j = i
                    while j < len(all_words):
                        chunk.append(all_words[j])
                        chunk_text = " ".join([w.word.strip() for w in chunk])
                        
                        gap = 0
                        if j < len(all_words) - 1:
                            gap = all_words[j+1].start - all_words[j].end
                        
                        is_last_chunk_word = (j == len(all_words) - 1)
                        
                        # Decide to break the chunk for Cinematic Look (15-22 chars)
                        if gap > 0.5 or len(chunk_text) > 22 or is_last_chunk_word:
                            break
                        
                        # Optimization: if next word starts a match, stop here
                        if j + 1 < len(all_words):
                            # (Optional check for next match start omitted for brevity/speed)
                            pass
                        j += 1
                    
                    srt_items.append({
                        "start_raw": chunk_start,
                        "end_raw": all_words[j].end,
                        "text": self.filter_profanity(chunk_text)
                    })
                    i = j + 1 # CONSUME
        
        # FINAL PASS: Physical Audio Audit & Linearization
        print(f"[*] Post-Processing {len(srt_items)} segments for DaVinci Precise Alignment...")
        
        # 4.0 Core: Real Physical Audit using RMS energy
        srt_items = self.physical_audio_audit(audio_path, srt_items)
        
        # Linearize and resolve overlaps
        final_srt = []
        last_end = 0
        
        for i, item in enumerate(srt_items):
            corrected_text, song_tag, ratio = self.smart_correct(item['text'])
            text = corrected_text if song_tag else item['text']
            
            start = item['start_raw']
            end = item['end_raw']
            
            # DaVinci Safety: 20ms minimal padding between blocks
            if start < last_end + 0.02:
                start = last_end + 0.02
            
            if end <= start:
                end = start + 0.5
            
            final_srt.append({
                "index": i + 1,
                "start": self.format_timestamp(start),
                "end": self.format_timestamp(end),
                "text": text
            })
            last_end = end

        return final_srt

    def physical_audio_audit(self, audio_path, items):
        """V5.0: Advanced Spectral Onset Snapping & Beat-Syncing."""
        try:
            print(f"[*] V5.0 Physical Audit: Analyzing spectral flux for {os.path.basename(audio_path)}")
            y, sr = librosa.load(audio_path, sr=16000)
            
            # 1. Onset Detection (Spectral Flux based)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time')
            
            # 2. Beat Tracking (for grid snapping)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            beat_times = librosa.frames_to_time(beats, sr=sr)
            
            refined_items = []
            for item in items:
                orig_start = item['start_raw']
                orig_end = item['end_raw']
                
                # Snap Start to nearest ONSET (within 300ms window)
                # We prioritize onsets as they represent the literal vocal start
                valid_onsets = onsets[(onsets >= orig_start - 0.3) & (onsets <= orig_start + 0.3)]
                if len(valid_onsets) > 0:
                    # Pick the strongest onset if possible or nearest
                    new_start = valid_onsets[np.argmin(np.abs(valid_onsets - orig_start))]
                    item['start_raw'] = new_start
                
                # Snap End to nearest BEAT or ONSET (within 400ms window)
                # Snapping to beat makes transitions feel musical
                combined_anchors = np.concatenate([onsets, beat_times])
                valid_anchors = combined_anchors[(combined_anchors >= orig_end - 0.4) & (combined_anchors <= orig_end + 0.4)]
                
                if len(valid_anchors) > 0:
                    new_end = valid_anchors[np.argmin(np.abs(valid_anchors - orig_end))]
                    item['end_raw'] = max(item['start_raw'] + 0.3, new_end)
                
                # Resolve potential logic errors
                if item['end_raw'] <= item['start_raw']:
                    item['end_raw'] = item['start_raw'] + 0.5
                    
                refined_items.append(item)
                
            return refined_items
        except Exception as e:
            print(f"[!] V5.0 Physical Audit Failed: {e}. Falling back.")
            import traceback
            traceback.print_exc()
            return items

    def smart_correct(self, text):
        """Fuzzy match with official lyrics database and apply profanity filter."""
        # 1. Profanity Filter (Streaming Style)
        text = self.filter_profanity(text)
        
        best_ratio = 0
        best_match = text
        best_tag = ""
        
        # Flattened search for all songs
        for song_tag, lines in self.LYRIC_CONTEXT.items():
            for line in lines:
                # Apply filter to official lyrics too just in case
                clean_line = self.filter_profanity(line)
                ratio = SequenceMatcher(None, text.lower(), clean_line.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = clean_line
                    best_tag = song_tag.replace("_", " ")

        # Threshold for correction
        if best_ratio > 0.6: 
            return best_match, best_tag, best_ratio
        return text, "", best_ratio

    def filter_profanity(self, text):
        """Streaming Platform Style: Replace sensitive words with **."""
        # A list of common raw words to filter in Hip-Hop/Pop contexts
        # In a real scenario, this would be a much larger external list
        PROFANITY_LIST = [
            "fuck", "sh*t", "shit", "bitch", "damn", "ass", 
            "motherfucker", "nigga", "hell", "pussy"
        ]
        
        import re
        words = text.split()
        clean_words = []
        for word in words:
            # Strip punctuation for comparison
            base_word = re.sub(r'[^\w\s]', '', word).lower()
            if base_word in PROFANITY_LIST:
                # Replace with asterisks of matching length or standard **
                clean_words.append("*" * len(word))
            else:
                clean_words.append(word)
        
        return " ".join(clean_words)

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
    import argparse
    parser = argparse.ArgumentParser(description="Subtitle Lab 3.0 Engine")
    parser.add_argument("audio_path", help="Path to audio file")
    parser.add_argument("--songs", help="Comma separated song keys for context")
    parser.add_argument("--model", default="base", help="Whisper model size (base, small, medium, large-v3)")
    parser.add_argument("--skip-sep", action="store_true", help="Skip vocal separation for speed")
    parser.add_argument("--lang", help="Force specific language (e.g. ko, ja, zh, en)")
    
    args = parser.parse_args()

    input_file = args.audio_path
    song_keys = args.songs.split(",") if args.songs else None

    engine = SubtitleEngineV3(model_size=args.model)
    
    processing_file = input_file
    if not args.skip_sep:
        try:
            processing_file = engine.separate_vocals_mdx(input_file)
        except Exception as e:
            print(f"[!] Separation failed, falling back to original: {e}")
            processing_file = input_file
    else:
        print("[*] Skipping separation as requested.")

    results = engine.transcribe_with_context(processing_file, song_keys, language=args.lang)
    
    output_srt = os.path.splitext(input_file)[0] + "_3.0.srt"
    engine.export_srt(results, output_srt)
