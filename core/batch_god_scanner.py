import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Path setup
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from mastering_core import MasteringAnalyzer
from cache_manager import load_cache, save_cache_atomic

class BatchGodScanner:
    def __init__(self, cache_path=None):
        self.cache_path = cache_path or r"d:\anti\scripts\song_analysis_cache.json"
        self.cache = load_cache(self.cache_path)
        self.analyzer = MasteringAnalyzer()
        self.updated_count = 0
        self.error_count = 0
        
    def is_god_mode_ready(self, analysis_data):
        """
        Check if the track already has God Mode DNA.
        Criteria: Has 'sonic_dna' AND contains more than just generic 5 YAMNet tags.
        """
        dna = analysis_data.get('sonic_dna', [])
        if not dna:
            return False
            
        # Generic YAMNet tags often appear in small clusters (Music, Genre, etc.)
        # God Mode usually returns 10+ tags across 8 dimensions
        if len(dna) < 6:
            return False
            
        # Check for presence of specialized instruction tags (highly likely God Mode)
        special_keys = ["Whispering", "Boxy", "Swing", "Dorian", "Vintage", "Warm", "Aggressive_Flow"]
        for k in special_keys:
             if any(k in str(t) for t in dna):
                 return True
                 
        return False

    async def run_scan(self, target_folder=None, throttle_sec=1.0, safe_mode=False):
        print(f"🚀 [God Mode Scanner] Starting GLOBAL evolution process (Eco-Mode)...")
        print(f"📂 Cache: {self.cache_path} ({len(self.cache)} records)")
        print(f"🐢 Throttle: {throttle_sec}s delay between tracks")
        if safe_mode:
            print(f"🛡️ SAFE MODE: Extended cooling enabled.")
        
        # 1. Identify targets
        targets = []
        for key, entry in self.cache.items():
            fpath = entry.get('file_path')
            
            if target_folder and target_folder.lower() not in fpath.lower():
                continue
                
            if not fpath or not os.path.exists(fpath):
                continue
                
            analysis = entry.get('analysis', {})
            if 'god_mode_details' in analysis:
                continue
                
            targets.append((key, fpath))
        
        print(f"🎯 Need to upgrade: {len(targets)} tracks")
        print(f"{'='*60}")
        
        # 2. Process Batch
        for i, (key, fpath) in enumerate(targets):
            print(f"[{i+1}/{len(targets)}] 🧬 Upgrading DNA: {os.path.basename(fpath)}...")
            try:
                # Perform the God Mode Scan (V33.8 with Cache)
                new_dna_results = self.analyzer.extract_sonic_dna(fpath)
                
                flat_tags = []
                for dim, items in new_dna_results.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'tag' in item:
                                flat_tags.append(item['tag'])
                            elif isinstance(item, str): 
                                flat_tags.append(item)
                
                unique_tags = list(set(flat_tags))
                
                if unique_tags and "error" not in new_dna_results:
                    self.cache[key]['analysis']['sonic_dna'] = unique_tags
                    self.cache[key]['analysis']['god_mode_details'] = new_dna_results
                    
                    self.updated_count += 1
                    print(f"   ✅ Upgraded! (+{len(unique_tags)} dimensions detected)")
                    
                    if self.updated_count % 5 == 0:
                        save_cache_atomic(self.cache, self.cache_path)
                        print("   💾 Checkpoint saved.")
                
                # 3. Cooling Cycle
                # Extra pause every 10 tracks to let GPU fans catch up
                if i > 0 and i % 10 == 0:
                    cooldown = 10.0 if safe_mode else 5.0
                    print(f"   ❄️ [Cooling Cycle] Resting for {cooldown}s...")
                    await asyncio.sleep(cooldown)
                else:
                    if throttle_sec > 0:
                        await asyncio.sleep(throttle_sec)
                    
            except Exception as e:
                print(f"   ❌ Error scanning file: {e}")
                self.error_count += 1
                await asyncio.sleep(throttle_sec * 2) # Back off on error
                
        # Final Save
        save_cache_atomic(self.cache, self.cache_path)
        print(f"{'='*60}")
        print(f"🎉 Evolution Complete!")
        print(f"✅ Upgraded: {self.updated_count} tracks")
        print(f"❌ Errors: {self.error_count}")
        print(f"🧠 System Intelligence: V33.7 God Mode (ACTIVE)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI DJ God Mode Batch Scanner")
    parser.add_argument("--folder", type=str, help="Target folder to scan (partial path match)")
    parser.add_argument("--throttle", type=float, default=1.0, help="Throttle delay in seconds between tracks")
    parser.add_argument("--safe", action="store_true", help="Enable extended cooling cycles")
    
    # Compatibility with previous direct folder arg
    args, unknown = parser.parse_known_args()
    
    target_folder = args.folder
    if not target_folder and len(unknown) > 0:
        target_folder = unknown[0]
        
    scanner = BatchGodScanner()
    asyncio.run(scanner.run_scan(target_folder, throttle_sec=args.throttle, safe_mode=args.safe))
