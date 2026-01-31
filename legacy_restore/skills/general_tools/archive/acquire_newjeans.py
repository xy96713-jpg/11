import os
import subprocess
import time
from pathlib import Path

def download_track(query, filename=None):
    script_path = r"d:\anti\skills\music_download_expert\scripts\download_and_tag.py"
    
    cmd = ["python", script_path, query]
    if filename:
        cmd.extend(["--name", filename])
        
    print(f"\n🚀 Launching download for: {query}")
    try:
        subprocess.run(cmd, check=True)
        print("✅ Download command completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download {query}: {e}")

def main():
    target_tracks = [
        # 1st EP
        {"query": "NewJeans Attention", "filename": "NewJeans - Attention"},
        {"query": "NewJeans Hype Boy", "filename": "NewJeans - Hype Boy"},
        {"query": "NewJeans Cookie", "filename": "NewJeans - Cookie"},
        {"query": "NewJeans Hurt", "filename": "NewJeans - Hurt"},
        
        # OMG
        {"query": "NewJeans Ditto", "filename": "NewJeans - Ditto"},
        {"query": "NewJeans OMG", "filename": "NewJeans - OMG"},
        
        # Get Up
        {"query": "NewJeans Super Shy", "filename": "NewJeans - Super Shy"},
        {"query": "NewJeans ETA", "filename": "NewJeans - ETA"},
        {"query": "NewJeans New Jeans", "filename": "NewJeans - New Jeans"},
        {"query": "NewJeans Cool With You", "filename": "NewJeans - Cool With You"},
        
        # How Sweet / Recent
        {"query": "NewJeans How Sweet", "filename": "NewJeans - How Sweet"},
        {"query": "NewJeans Bubble Gum", "filename": "NewJeans - Bubble Gum"},
    ]

    print(f"🤖 Starting Bulk Acquisition for {len(target_tracks)} NewJeans tracks...")
    
    for i, track in enumerate(target_tracks, 1):
        print(f"\n[{i}/{len(target_tracks)}] Processing...")
        download_track(track["query"], track["filename"])
        time.sleep(2) # Prevent rate limiting

    print("\n🎉 All tasks processed. Please verify in D:\\song\\Final_Music_Official")

if __name__ == "__main__":
    main()
