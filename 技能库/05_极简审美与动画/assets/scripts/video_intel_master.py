import sys
import os
import re
import json
import asyncio
import subprocess

class VideoIntelMaster:
    """The unified router for Antigravity Video Perception V6.1."""
    
    def __init__(self, url, output_base):
        self.url = url
        self.output_base = output_base
        self.scripts_dir = "D:\\anti\\skills\\douyin_intelligence\\scripts"
        os.makedirs(output_base, exist_ok=True)

    def is_douyin(self):
        """Detect if the URL belongs to Douyin/TikTok China ecosystem."""
        douyin_patterns = [
            r"douyin\.com",
            r"v\.douyin\.com",
            r"iesdouyin\.com"
        ]
        return any(re.search(p, self.url) for p in douyin_patterns)

    async def run(self):
        print(f"[*] Entering Intelligence Routing for: {self.url}", file=sys.stderr)
        
        # 1. Select Engine
        if self.is_douyin():
            print("[+] Douyin Domain Detected. Triggering 'Blue Light' CDP Wiretap...", file=sys.stderr)
            # Step A: Wiretap & Intercept Truth
            wiretap_cmd = [
                "python", os.path.join(self.scripts_dir, "wiretap_video.py"),
                self.url, self.output_base
            ]
            subprocess.run(wiretap_cmd, check=True)
            
            # Step B: Direct Binary Download from Truth
            json_path = os.path.join(self.output_base, "intercepted_truth.json")
            download_cmd = [
                "python", os.path.join(self.scripts_dir, "final_truth_downloader.py"),
                json_path, self.output_base
            ]
            res = subprocess.run(download_cmd, capture_output=True, text=True)
            try:
                download_info = json.loads(res.stdout)
                video_path = download_info.get("path")
            except:
                print("[!] Download failed or path not found.", file=sys.stderr)
                return
        else:
            print("[*] General Domain Detected. Using Standard Protocols...", file=sys.stderr)
            # Fallback to direct_video_downloader.py (which uses yt-dlp)
            # For brevity in this router, we assume standard downloader is ready
            # ... (Implementation similar to above but calling generic skills)
            return

        # 2. Universal V6.1 Perception (ASR/OCR/Visual)
        if video_path and os.path.exists(video_path):
            print("[+] Video Acquired. Initiating Full-Spectrum Reconstruction...", file=sys.stderr)
            v6_cmd = [
                "python", os.path.join(self.scripts_dir, "v6_full_spectrum.py"),
                video_path, self.output_base
            ]
            subprocess.run(v6_cmd, check=True)
            print(f"[SUCCESS] Total Perception Complete. Folder: {self.output_base}", file=sys.stderr)
        else:
            print("[!] Perception Failed: Asset not found.", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python video_intel_master.py <URL> <OUTPUT_DIR>")
        sys.exit(1)
    
    # Ensure environment is set for Playwright
    os.environ["HOME"] = "C:\\Users\\Administrator"
    
    master = VideoIntelMaster(sys.argv[1], sys.argv[2])
    asyncio.run(master.run())
