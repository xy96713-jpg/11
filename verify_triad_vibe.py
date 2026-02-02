
import asyncio
from typing import Dict, List

def calculate_vibe_score(t1: Dict, t2: Dict) -> float:
    """
    [V31.0 Prototype] Vibe-First Similarity Scorer.
    Prioritizes Timbre/Envelope over BPM/Key.
    """
    score = 0.0
    
    # 1. Timbre Envelope Check (Mocking YAMNet Spectral Analysis)
    env1 = t1.get('vibe', {}).get('envelope', 'unknown')
    env2 = t2.get('vibe', {}).get('envelope', 'unknown')
    
    if env1 == env2 and env1 == 'staccato_transient':
        print(f"  ✅ Envelope Lock: {env1}")
        score += 40.0 # Huge bonus for physical texture match
        
    # 2. Spectral Focus check
    bw1 = t1.get('vibe', {}).get('bandwidth', 'unknown')
    bw2 = t2.get('vibe', {}).get('bandwidth', 'unknown')
    
    if bw1 == bw2 and bw1 == 'narrow_mid':
        print(f"  ✅ Spectral Synergy: {bw1} (Clean Mix)")
        score += 20.0
        
    # 3. Cultural/Genre Tag (Lo-Fi Archetype)
    tags1 = t1.get('vibe', {}).get('tags', [])
    tags2 = t2.get('vibe', {}).get('tags', [])
    
    common = set(tags1).intersection(set(tags2))
    if "Lo-Fi_Pluck" in common:
        print(f"  ✅ Archetype Match: Lo-Fi Digital Pluck")
        score += 25.0
        
    # 4. BPM Tolerance (The V31.0 Logic)
    bpm1 = t1.get('bpm')
    bpm2 = t2.get('bpm')
    diff = abs(bpm1 - bpm2) / max(bpm1, bpm2)
    
    print(f"  ⚠️ BPM Gap: {diff*100:.1f}%")
    if diff > 0.15:
        if score > 50:
             print("  🔄 System Action: Suggest 'Elastic Stretch' or 'Half-Time Mix'")
             score -= 5.0 # Minor penalty compared to V30.0's rejection
        else:
             print("  ⛔ System Action: Reject (Gap too large for low texture match)")
             score -= 50.0

    return score

def audit_triad():
    print("🧪 V31.0 Triad Audit: Ninja x Foot Fungus x Ben Cao Gang Mu")
    print("Objectively analyzing 'Why this works' despite data clashes.\n")
    
    # Mock Data based on Deep Research
    ninja = {
        'title': 'Ninja',
        'bpm': 110,
        'vibe': {
            'envelope': 'staccato_transient',
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Oriental']
        }
    }
    
    foot_fungus = {
        'title': 'Foot Fungus',
        'bpm': 90, # Kenny Beats standard
        'vibe': {
            'envelope': 'staccato_transient', # Censor beep is short
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Cartoon']
        }
    }
    
    ben_cao = {
        'title': 'Ben Cao Gang Mu',
        'bpm': 94, # Jay Chou standard
        'vibe': {
            'envelope': 'staccato_transient', # Pipa plucks
            'bandwidth': 'narrow_mid',
            'tags': ['Lo-Fi_Pluck', 'Oriental']
        }
    }
    
    # Pair 1: Ninja x Foot Fungus
    print("--- [Pair 1] Ninja (110) x Foot Fungus (90) ---")
    s1 = calculate_vibe_score(ninja, foot_fungus)
    print(f"🏆 Vibe Score: {s1}/85\n")
    
    # Pair 2: Ninja x Ben Cao Gang Mu
    print("--- [Pair 2] Ninja (110) x Ben Cao Gang Mu (94) ---")
    s2 = calculate_vibe_score(ninja, ben_cao)
    print(f"🏆 Vibe Score: {s2}/85\n")
    
    # Pair 3: Foot Fungus x Ben Cao Gang Mu
    print("--- [Pair 3] Foot Fungus (90) x Ben Cao Gang Mu (94) ---")
    s3 = calculate_vibe_score(foot_fungus, ben_cao)
    print(f"🏆 Vibe Score: {s3}/85\n")

if __name__ == "__main__":
    audit_triad()
