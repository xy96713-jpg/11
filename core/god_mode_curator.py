import json
import os
import sys
import argparse
from typing import Dict, List, Tuple
from pathlib import Path

# Path setup
current_dir = Path(__file__).parent.parent # Root d:/anti
sys.path.insert(0, str(current_dir))

from skills.mashup_intelligence.scripts.core import SonicMatcher

class GodModeCurator:
    """The Strongest Brain (V34.0) - Multidimensional Point-Cloud Curator"""
    
    def __init__(self, cache_path: str = r"d:\anti\scripts\song_analysis_cache.json"):
        self.cache_path = cache_path
        with open(cache_path, 'r', encoding='utf-8') as f:
            self.cache = json.load(f)
        self.matcher = SonicMatcher()
        print(f"🧠 [X-Ray] Engine Online. Library Size: {len(self.cache)} tracks.")

    def find_matches(self, seed_query: str, limit: int = 5) -> List[Dict]:
        """Find the best God-Mode matches for a seed track"""
        
        # 1. Identify seed track
        seed_key = None
        for key, data in self.cache.items():
            fpath = data.get('file_path', '')
            if seed_query.lower() in fpath.lower() or seed_query.lower() in key.lower():
                seed_key = key
                break
        
        if not seed_key:
            print(f"❌ Seed track not found: {seed_query}")
            return []
            
        seed_data = self.cache[seed_key]
        seed_analysis = seed_data.get('analysis', {})
        seed_god = seed_analysis.get('god_mode_details', {})
        
        print(f"🎯 Seed Target: {os.path.basename(seed_key)}")
        print(f"🧬 Seed DNA Alpha: {seed_analysis.get('sonic_dna', [])[:5]}...")

        matches = []
        
        # 2. Iterate and Match
        for key, target_data in self.cache.items():
            if key == seed_key: continue
            
            target_analysis = target_data.get('analysis', {})
            target_god = target_analysis.get('god_mode_details', {})
            
            # Use the V33.7 Axiom Matcher
            score, reasons = self.matcher.calculate_bonus(seed_analysis, target_analysis)
            
            # Enhanced X-Ray Metrics: Deep DNA Similarity
            dna_synergy_score = 0.0
            shared_tech = []
            
            # Check Hardware/Synthesis Synergies
            seed_hw = set([h['tag'].lower() for h in seed_god.get('hardware', [])])
            target_hw = set([h['tag'].lower() for h in target_god.get('hardware', [])])
            intersect_hw = seed_hw.intersection(target_hw)
            
            if intersect_hw:
                dna_synergy_score += len(intersect_hw) * 15.0
                shared_tech.extend(list(intersect_hw))
            
            # Final Score Calculation
            final_score = 50.0 + score + dna_synergy_score # Base 50
            
            # Simple BPM/Key penalty for curation (optional)
            bpm1 = seed_analysis.get('bpm', 120)
            bpm2 = target_analysis.get('bpm', 120)
            if abs(bpm1 - bpm2) > 10: final_score -= 20
            
            matches.append({
                "file": key,
                "name": os.path.basename(key),
                "score": round(final_score, 1),
                "reasons": reasons,
                "shared_dna": shared_tech,
                "god_details": target_god
            })
            
        # 3. Sort and Return
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:limit]

    def generate_xray_report(self, seed_query: str, limit: int = 5):
        """Generate a human-readable X-Ray Curation Report"""
        results = self.find_matches(seed_query, limit)
        if not results: return
        
        report_path = f"d:/生成的set/XRAY_REPORT_{seed_query}.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🧬 Project X-Ray: God-Mode Curation Report\n\n")
            f.write(f"**Seed Track**: {seed_query}\n")
            f.write(f"**Curator Version**: V34.1 (Strongest Brain - 2026 Synergy)\n")
            f.write(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"---\n\n")
            
            for i, m in enumerate(results):
                f.write(f"## {i+1}. {m['name']}\n")
                f.write(f"- **Match Score**: `{m['score']}/100` 🏆\n")
                f.write(f"- **Mixing Axioms**:\n")
                for r in m['reasons']:
                    f.write(f"  - {r}\n")
                
                if m['shared_dna']:
                    f.write(f"- **Atomic DNA Sync**: `{', '.join(m['shared_dna'])}` (Hardware/Spectral Match)\n")
                
                f.write(f"\n```json\n// Detected God-Mode Insights\n")
                f.write(json.dumps(m['god_details'], indent=2, ensure_ascii=False))
                f.write(f"\n```\n\n")
        
        print(f"✅ X-Ray Report Generated: {report_path}")
        return report_path

if __name__ == "__main__":
    from datetime import datetime
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=str, required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    
    curator = GodModeCurator()
    curator.generate_xray_report(args.seed, args.limit)
