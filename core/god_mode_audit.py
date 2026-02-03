#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[GOD MODE] Audio Intelligence Audit Report Tool (V33.6)
======================================================
Generates a high-precision technical report focusing on Vocals, 
Hardware Signatures, Musicology, and Spatial DNA.
"""

import sys
import os
import json
from mastering_core import MasteringAnalyzer

def print_banner(title):
    print("\n" + "="*80)
    print(f" {title.center(78)} ")
    print("="*80)

def format_dna(dna):
    if not dna:
        print(" [!] No DNA extracted.")
        return

    sections = {
        "vocals": "🎤 VOCAL DNA (Performance & Tone)",
        "hardware": "🎚️ HARDWARE & ENGINEERING (Analog/Digital Signatures)",
        "musicology": "🎼 MUSICOLOGY & MODAL DNA (Theory & Rhythm)",
        "spatial": "🌌 SPATIAL & ACOUSTIC (Environment & Width)",
        "production_era": "🕰️ PRODUCTION ERA & CULTURE",
        "synthesis": "🎹 SYNTHESIS & SOUND DESIGN",
        "genres": "🏷️ STYLE & GENRE (Discogs 400)",
        "instruments": "🎸 INSTRUMENTATION"
    }

    for key, title in sections.items():
        hits = dna.get(key, [])
        print(f"\n{title}")
        if not hits:
            print("  - None detected with high confidence.")
            continue
        
        for hit in hits:
            bar = "█" * int(hit['score'] * 40)
            score_str = f"({hit['score']:.3f})"
            print(f"  ▸ {hit['tag']:<30} {score_str:<10} {bar}")

def run_god_audit(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return

    print_banner("GOD MODE AUDIO INTELLIGENCE AUDIT")
    print(f" Target: {os.path.basename(file_path)}")
    print(f" Path:   {os.path.abspath(file_path)}")
    
    analyzer = MasteringAnalyzer()
    print("\n [Inference] Running multidimensional Sonic DNA extraction...")
    dna = analyzer.extract_sonic_dna(file_path)
    
    print_banner("ANALYSIS RESULTS")
    format_dna(dna)
    print_banner("AUDIT COMPLETE")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python god_mode_audit.py <file_path>")
        sys.exit(1)
    
    run_god_audit(sys.argv[1])
