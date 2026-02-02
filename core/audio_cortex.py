
# -*- coding: utf-8 -*-
"""
V30.0 True Sonic Intelligence Core
Handles DSP analysis using Essentia (MusiCNN) and TensorFlow.
Implements Lazy Loading to prevent slow startup times.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import time
import numpy as np

# Brain Path
BRAIN_DIR = Path("C:/Users/Administrator/.gemini/antigravity/brain/1f558f2e-7c89-4811-8e59-b7a3c56f634e")
CACHE_FILE = BRAIN_DIR / "sonic_fingerprints.json"

class AudioCortex:
    _instance = None
    _is_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioCortex, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if AudioCortex._is_initialized:
            return
            
        self.logger = logging.getLogger("AudioCortex")
        self.cache = self._load_cache()
        self.dsp_engine = None # Lazy loaded
        AudioCortex._is_initialized = True
        
    def _load_cache(self) -> Dict:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load sonic cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save sonic cache: {e}")

    def _init_dsp_engine(self):
        """Lazy load heavy libraries (Librosa/TF) only when needed."""
        if self.dsp_engine:
            return
            
        print("[AudioCortex] Initializing V30.1 DSP Engine (Librosa/YAMNet)...")
        try:
            # [REAL IMPLEMENTATION - PIVOT TO LIBROSA/YAMNET]
            import librosa
            import tensorflow as tf
            import tensorflow_hub as hub
            import numpy as np
            
            # Load YAMNet model from TF Hub
            # Note: This might download 20MB+ on first run
            self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
            self.class_map_path = self.yamnet_model.class_map_path().numpy()
            
            print(f"[AudioCortex] Engine Loaded. Librosa: {librosa.__version__}, TF: {tf.__version__}")
            self.dsp_engine = "Active"
        except ImportError as e:
             print(f"[AudioCortex] DSP Libraries missing: {e}")
             self.dsp_engine = None
        except Exception as e:
             print(f"[AudioCortex] Engine Init Failed: {e}")
             self.dsp_engine = None

    def analyze_track(self, file_path: str, force_refresh: bool = False) -> Dict:
        """
        Main Analysis Entry Point.
        Returns cached analysis or performs new analysis.
        """
        filename = os.path.basename(file_path)
        
        # 1. Check Cache
        if not force_refresh and filename in self.cache:
            return self.cache[filename]
            
        # 2. Perform Analysis
        self._init_dsp_engine()
        
        if not self.dsp_engine:
            return {} 
            
        print(f"[AudioCortex] Hearing: {filename}...")
        
        try:
            import librosa
            import numpy as np
            
            # --- V30.1 DSP Pipeline (Librosa) ---
            # 1. Load Audio
            y, sr = librosa.load(file_path, sr=16000) # YAMNet expects 16kHz
            
            # 2. Tempo/Beat
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Fix for Librosa 0.10+ where tempo is an array
            if isinstance(tempo, np.ndarray):
                tempo = tempo.item() if tempo.ndim == 0 else tempo[0]
            
            # 3. YAMNet Inference (Instrument Classification)
            # Run the model (expects normalized mono waveform)
            scores, embeddings, spectrogram = self.yamnet_model(y)
            
            # Process predictions
            # Scores is [N, 521] where N is number of frames (approx every 0.48s)
            # We average scores across the track
            mean_scores = np.mean(scores, axis=0)
            top_class_indices = np.argsort(mean_scores)[::-1][:5] # Top 5
            
            # Load class names
            import csv
            class_names = []
            with open(self.class_map_path) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    class_names.append(row['display_name'])
            
            detected_instruments = [class_names[i] for i in top_class_indices]
            
            # 4. Energy (Arousal Proxy)
            rms = librosa.feature.rms(y=y)
            avg_rms = float(np.mean(rms))
            # Normalize RMS to a 0.0-1.0 scale (approximate)
            arousal_proxy = min(1.0, avg_rms * 5.0) 
            
            analysis_result = {
                "instruments": detected_instruments,
                "dsp_estimated_bpm": float(tempo),
                "arousal_proxy": arousal_proxy,
                "analyzed_at": time.time(),
                "engine": "Librosa/YAMNet V30.1 + RMS Energy"
            }
            
            print(f"[AudioCortex] Analysis Complete. Est. BPM: {float(tempo):.1f}, Tags: {detected_instruments[:3]}")
            
            # 3. Update Cache
            self.cache[filename] = analysis_result
            self._save_cache()
            
            return analysis_result
            
        except Exception as e:
            print(f"[AudioCortex] Analysis Failed: {e}")
            return {}

    def get_sonic_tags(self, file_path: str) -> List[str]:
        data = self.analyze_track(file_path)
        tags = []
        if data:
            tags.extend(data.get("instruments", []))
            if "dsp_estimated_bpm" in data:
                # [V31.0 Policy] Explicitly mark as Estimate
                tags.append(f"{int(data['dsp_estimated_bpm'])}_BPM_DSP_Est")
        return [t for t in tags if t]

# Singleton Accessor
cortex = AudioCortex()
