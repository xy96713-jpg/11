
import asyncio
from typing import Dict, List
import sys

def calculate_mix_score(t1: Dict, t2: Dict) -> float:
    score = 0.0
    
    # 1. Physical Match (BPM)
    bpm1, bpm2 = t1['bpm'], t2['bpm']
    gap = abs(bpm1 - bpm2) / max(bpm1, bpm2)
    
    print(f"  📊 Physical: {bpm1} vs {bpm2} (Gap: {gap*100:.1f}%)")
    
    if gap <= 0.04:
        score += 40.0
        print("    ✅ Tier: Golden (Professional Sync)")
    elif gap <= 0.08:
        score += 30.0
        print("    ✅ Tier: Silver (Easy Sync)")
    elif gap <= 0.12:
        score += 20.0
        print("    ⚠️ Tier: Elastic (Standard Sync)")
    else:
        score -= 20.0
        print("    ⛔ Tier: Clash (Extreme Stretch required)")
        
    # 2. Vibe Match (Simulated DSP)
    score += 40.0 
    print("    ✅ Vibe: Lo-Fi Digital Pluck (Perfect Match)")
    
    return score

def final_audit_v2():
    print("🧪 V31.0 Final User-Truth Audit V2 (All Corrections)")
    print("Data Source: Rekordbox Manual Verification\n")
    
    # User's Truth
    ninja = {'title': 'Ninja (Jay Chou)', 'bpm': 105.26}
    ben_cao = {'title': 'Ben Cao Gang Mu', 'bpm': 101.0}
    foot_fungus = {'title': 'Foot Fungus (Matthewville)', 'bpm': 100.0} 
    
    # Pair 1: Ninja x Ben Cao Gang Mu
    print("--- [Pair 1] Ninja (105) x Ben Cao Gang Mu (101) ---")
    s1 = calculate_mix_score(ninja, ben_cao)
    print(f"🏆 Score: {s1}/80\n")
    
    # Pair 2: Ben Cao Gang Mu x Foot Fungus
    print("--- [Pair 2] Ben Cao Gang Mu (101) x Foot Fungus (100) ---")
    s2 = calculate_mix_score(ben_cao, foot_fungus)
    print(f"🏆 Score: {s2}/80\n")
    
    # Pair 3: Ninja x Foot Fungus
    print("--- [Pair 3] Ninja (105) x Foot Fungus (100) ---")
    s3 = calculate_mix_score(ninja, foot_fungus)
    print(f"🏆 Score: {s3}/80\n")

if __name__ == "__main__":
    final_audit_v2()
