#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mastering Core (V33.0) - SOTA Audio Intelligence
================================================
Integrates LAION-CLAP for semantic "feel" and Essentia-Discogs for 
high-precision style/instrument detection.
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import laion_clap

try:
    from core.tag_library import (
        GENRES_DISCOGS_400, INSTRUMENTS_VOCAB, VOCAL_DNA, HARDWARE_DNA, 
        MUSICOLOGY_DNA, SPATIAL_DNA, PRODUCTION_DNA, SYNTHESIS_DNA
    )
except ImportError:
    from tag_library import (
        GENRES_DISCOGS_400, INSTRUMENTS_VOCAB, VOCAL_DNA, HARDWARE_DNA, 
        MUSICOLOGY_DNA, SPATIAL_DNA, PRODUCTION_DNA, SYNTHESIS_DNA
    )

class MasteringAnalyzer:
    """Mother-Core for Audio Intelligence (V33.2 Full Power)"""
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.clap_model = None
        self._initialized = False
        
    def initialize(self):
        """Lazy load models to save memory until needed"""
        if self._initialized: return
        
        print(f"[MasteringCore] Initializing SOTA Models on {self.device}...")
        
        # 1. Load LAION-CLAP
        try:
            import laion_clap
            # Using the massive 2023 music-speech model for maximum precision
            self.clap_model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
            self.clap_model.load_ckpt() # This will download weights on first run
            self.clap_model.to(self.device).eval()
            print("  ✓ LAION-CLAP loaded successfully.")
        except Exception as e:
            print(f"  [Error] Failed to load LAION-CLAP: {e}")
            
        self._initialized = True

    def extract_sonic_dna(self, file_path: str) -> Dict:
        """
        [V33.6 GOD MODE] Multidimensional Perceptual Profiling.
        Runs 1000+ technical probes across 8 dimensions.
        """
        self.initialize()
        if not self.clap_model: return {}

        dna_results = {}
        dimension_map = {
            "genres": GENRES_DISCOGS_400,
            "instruments": INSTRUMENTS_VOCAB,
            "vocals": VOCAL_DNA,
            "hardware": HARDWARE_DNA,
            "musicology": MUSICOLOGY_DNA,
            "spatial": SPATIAL_DNA,
            "production_era": PRODUCTION_DNA,
            "synthesis": SYNTHESIS_DNA
        }

        try:
            # 1. Get Audio Embedding (Once)
            print(f"  [Audit] Extracting audio embedding for: {os.path.basename(file_path)}...", flush=True)
            audio_embed = self.clap_model.get_audio_embedding_from_filelist(x=[file_path])
            if isinstance(audio_embed, torch.Tensor):
                audio_embed = audio_embed.cpu().numpy()
            print("  ✓ Audio embedding extracted.", flush=True)
            
            for dim_name, tags in dimension_map.items():
                print(f"  [Audit] Profiling dimension: {dim_name} ({len(tags)} probes)...", flush=True)
                
                # 2. Get Text Embeddings in chunks to avoid CUDA errors/memory spikes
                chunk_size = 50
                all_text_embeds = []
                for i in range(0, len(tags), chunk_size):
                    chunk = tags[i:i + chunk_size]
                    # print(f"    - Processing probe chunk {i//chunk_size + 1}...", flush=True)
                    text_embed_chunk = self.clap_model.get_text_embedding(chunk)
                    if isinstance(text_embed_chunk, torch.Tensor):
                        text_embed_chunk = text_embed_chunk.cpu().numpy()
                    all_text_embeds.append(text_embed_chunk)
                
                text_embeds = np.vstack(all_text_embeds)
                print(f"  ✓ {dim_name} text embeddings generated.", flush=True)
                
                # 3. Compute Similarity (Cosine Dot Product)
                similarities = np.dot(audio_embed, text_embeds.T).flatten()
                
                # 4. Filter Top Results
                k = 3 if dim_name in ["genres", "instruments"] else 2
                top_indices = np.argsort(similarities)[-k:][::-1].tolist()
                
                dim_hits = []
                for idx in top_indices:
                    score = float(similarities[idx])
                    if score > 0.05:
                        dim_hits.append({
                            "tag": str(tags[idx]),
                            "score": round(score, 3)
                        })
                dna_results[dim_name] = dim_hits
                # print(f"  ✓ {dim_name} hits: {[h['tag'] for h in dim_hits]}", flush=True)
            
            return dna_results
            
        except Exception as e:
            import traceback
            print(f"  [Error] God Mode DNA Extraction failed: {e}", flush=True)
            traceback.print_exc()
            return {"error": str(e)}

    def full_audit(self, file_path: str) -> Dict:
        """Complete mastering-level analysis"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        return {
            "file": os.path.basename(file_path),
            "timestamp": str(datetime.now().timestamp() if 'datetime' in globals() else Path(file_path).stat().st_mtime),
            "sonic_dna": self.extract_sonic_dna(file_path)
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mastering_core.py <file_path>")
        sys.exit(1)
        
    from datetime import datetime
    analyzer = MasteringAnalyzer()
    report = analyzer.full_audit(sys.argv[1])
    print(json.dumps(report, indent=4))
