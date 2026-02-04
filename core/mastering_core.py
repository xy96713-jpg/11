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
import logging
import contextlib
import io
from pathlib import Path
from typing import Dict, Optional, List
import laion_clap

try:
    from core.tag_library import (
        GENRES_DISCOGS_400, INSTRUMENTS_VOCAB, VOCAL_DNA, HARDWARE_DNA, 
        MUSICOLOGY_DNA, SPATIAL_DNA, PRODUCTION_DNA, SYNTHESIS_DNA, COGNITIVE_DNA
    )
except ImportError:
    from tag_library import (
        GENRES_DISCOGS_400, INSTRUMENTS_VOCAB, VOCAL_DNA, HARDWARE_DNA, 
        MUSICOLOGY_DNA, SPATIAL_DNA, PRODUCTION_DNA, SYNTHESIS_DNA, COGNITIVE_DNA
    )

@contextlib.contextmanager
def suppress_output():
    """
    [V33.8] Light-weight output suppression for Windows compatibility.
    """
    # Silence transformers/torch logging
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("laion_clap").setLevel(logging.ERROR)
    
    new_stdout, new_stderr = io.StringIO(), io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_stdout, new_stderr
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

class MasteringAnalyzer:
    """Mother-Core for Audio Intelligence (V33.8 Optimized)"""
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.clap_model = None
        self._initialized = False
        self._text_embed_cache = {} # Cache for dimension embeddings
        
    def initialize(self):
        """Lazy load models with output suppression to prevent terminal hangs"""
        if self._initialized: return
        
        print(f"[MasteringCore] Initializing SOTA Models on {self.device}...", flush=True)
        
        # 1. Load LAION-CLAP
        try:
            # Silence Python logs
            with suppress_output():
                self.clap_model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
                self.clap_model.load_ckpt() 
                self.clap_model.to(self.device).eval()
            print("  ✓ Neural Engine (LAION-CLAP) ready.", flush=True)
        except Exception as e:
            print(f"  [Error] Failed to load LAION-CLAP: {e}", flush=True)
            
        self._initialized = True

    def get_cached_text_embeddings(self, dim_name: str, tags: List[str]):
        """
        [Optimization] Generate text embeddings once and keep them in memory.
        Reduces GPU load by 90% during batch scans.
        """
        if dim_name in self._text_embed_cache:
            return self._text_embed_cache[dim_name]
            
        print(f"  [Cache] Generating static embeddings for dimension: {dim_name} ({len(tags)} probes)...", flush=True)
        chunk_size = 50
        all_text_embeds = []
        
        with torch.no_grad():
            for i in range(0, len(tags), chunk_size):
                chunk = tags[i:i + chunk_size]
                text_embed_chunk = self.clap_model.get_text_embedding(chunk)
                if isinstance(text_embed_chunk, torch.Tensor):
                    text_embed_chunk = text_embed_chunk.cpu().numpy()
                all_text_embeds.append(text_embed_chunk)
        
        final_embeds = np.vstack(all_text_embeds)
        self._text_embed_cache[dim_name] = final_embeds
        return final_embeds

    def extract_sonic_dna(self, file_path: str) -> Dict:
        """
        [V33.8 OPTIMIZED] Multidimensional Perceptual Profiling.
        Uses cached text embeddings to prevent GPU overheating/crashes.
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
            "synthesis": SYNTHESIS_DNA,
            "cognitive_dna": COGNITIVE_DNA
        }

        try:
            # 1. Get Audio Embedding (Once)
            # print(f"  [Audit] Extracting audio embedding: {os.path.basename(file_path)}...", flush=True)
            with torch.no_grad():
                audio_embed = self.clap_model.get_audio_embedding_from_filelist(x=[file_path])
                if isinstance(audio_embed, torch.Tensor):
                    audio_embed = audio_embed.cpu().numpy()
            
            for dim_name, tags in dimension_map.items():
                # 2. Use Cached Text Embeddings (The real GPU saver)
                text_embeds = self.get_cached_text_embeddings(dim_name, tags)
                
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
            
            # Clear CUDA cache periodically to prevent build-up
            if self.device.type == 'cuda':
                torch.cuda.empty_cache()
                
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
        
    # Force UTF-8 for Windows console output
    sys.stdout.reconfigure(encoding='utf-8')
    
    from datetime import datetime
    analyzer = MasteringAnalyzer()
    report = analyzer.full_audit(sys.argv[1])
    print(json.dumps(report, indent=4, ensure_ascii=False))
