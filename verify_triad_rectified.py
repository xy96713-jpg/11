
import asyncio
from typing import Dict, List

def normalize_bpm(bpm: float) -> float:
    """
    [V31.0 Logic] Normalize BPM to a standard 70-140 analysis range.
    Handles 'Halftime/Doubletime' ambiguity.
    """
    if bpm > 130:
        return bpm / 2.0
    if bpm < 65:
        return bpm * 2.0
    return bpm

def calculate_vibe_score(t1: Dict, t2: Dict) -> float:
    score = 0.0
    
    # 1. Timbre Envelope Check (Mocking YAMNet Spectral Analysis)
    env1 = t1.get('vibe', {}).get('envelope', 'unknown')
    env2 = t2.get('vibe', {}).get('envelope', 'unknown')
    
    if env1 == env2 and env1 == 'staccato_transient':
        score += 40.0 
        
    # 2. Spectral Focus check
    bw1 = t1.get('vibe', {}).get('bandwidth', 'unknown')
    bw2 = t2.get('vibe', {}).get('bandwidth', 'unknown')
    
    if bw1 == bw2 and bw1 == 'narrow_mid':
        score += 20.0
        
    # 3. Cultural/Genre Tag (Lo-Fi Archetype)
    tags1 = t1.get('vibe', {}).get('tags', [])
    tags2 = t2.get('vibe', {}).get('tags', [])
    
    common = set(tags1).intersection(set(tags2))
    if "Lo-Fi_Pluck" in common:
        score += 25.0
        
    # 4. BPM Tolerance (V31.0: Normalized)
    raw_bpm1, raw_bpm2 = t1.get('bpm'), t2.get('bpm')
    n_bpm1, n_bpm2 = normalize_bpm(raw_bpm1), normalize_bpm(raw_bpm2)
    
    diff = abs(n_bpm1 - n_bpm2) / max(n_bpm1, n_bpm2)
    
    print(f"  📊 BPM Analysis: {raw_bpm1} vs {raw_bpm2} -> Normalized: {n_bpm1} vs {n_bpm2}")
    print(f"  ⚠️ Normalized Gap: {diff*100:.1f}%")
    
    if diff > 0.15:
        if score > 50:
             print("  🔄 System Action: Suggest 'Elastic Stretch' or 'Half-Time Mix'")
             score -= 5.0 
        else:
             print("  ⛔ System Action: Reject (Gap too large for low texture match)")
             score -= 50.0

    return score

def audit_triad_corrected():
    print("🧪 V31.0 Corrected Triad Audit (Authentic Data)")
    print("Correcting previous BPM errors with 'Halftime Normalization'.\n")
    
    # Authentic Data
    ninja = {
        'title': 'Ninja (7981 Kal)',
        'bpm': 142, # Drill Tempo (Doubletime)
        'vibe': {
            'envelope': 'staccato_transient',
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Oriental']
        }
    }
    
    foot_fungus = {
        'title': 'Foot Fungus (Ski Mask)',
        'bpm': 154, # Trap Tempo (Doubletime)
        'vibe': {
            'envelope': 'staccato_transient', 
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Cartoon']
        }
    }
    
    ben_cao = {
        'title': 'Ben Cao Gang Mu (Jay Chou)',
        'bpm': 94, # Hip-Hop Standard
        'vibe': {
            'envelope': 'staccato_transient',
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Oriental']
        }
    }
    
    # Pair 1: Ninja x Foot Fungus
    print("--- [Pair 1] Ninja (142) x Foot Fungus (154) ---")
    s1 = calculate_vibe_score(ninja, foot_fungus)
    print(f"🏆 Vibe Score: {s1}/85\n")
    
    # Pair 2: Ninja x Ben Cao Gang Mu
    print("--- [Pair 2] Ninja (142) x Ben Cao Gang Mu (94) ---")
    # 142 -> 71. 94 vs 71 is a 24% gap. Huge.
    s2 = calculate_vibe_score(ninja, ben_cao)
    print(f"🏆 Vibe Score: {s2}/85\n")
    
    # Pair 3: Foot Fungus x Ben Cao Gang Mu
    print("--- [Pair 3] Foot Fungus (154) x Ben Cao Gang Mu (94) ---")
    # 154 -> 77. 94 vs 77 is a 18% gap. Still large.
    s3 = calculate_vibe_score(foot_fungus, ben_cao)
    print(f"🏆 Vibe Score: {s3}/85\n")

if __name__ == "__main__":
    audit_triad_corrected()
