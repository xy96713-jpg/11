import sys
import os
import subprocess
import yt_dlp

def download_url(url, output_filename=None):
    print(f"\n🚀 [SoundCloud Path] Downloading: {url}")
    
    output_dir = r"D:\song"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if output_filename:
        # If it doesn't end in .mp3, add it
        if not output_filename.lower().endswith(".mp3"):
            output_filename += ".mp3"
        output_template = f"{output_dir}/{output_filename}"
    else:
        output_template = f"{output_dir}/%(title)s.%(ext)s"
    
    # The "Stable" yt-dlp command derived from user preference
    cmd = [
        sys.executable, "-m", "yt_dlp",
        url,
        "-o", output_template,
        "--format", "mp3/bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "320K",
        "--no-playlist",
        "--force-overwrites"
    ]
    
    # Inject cookies if available
    cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
    if os.path.exists(cookie_path):
        cmd.extend(["--cookies", cookie_path])
        
    try:
        subprocess.run(cmd, check=True)
        print("✅ Download Success (MP3)")
        return True
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url_arg = sys.argv[1]
        name_arg = sys.argv[2] if len(sys.argv) > 2 else None
        download_url(url_arg, name_arg)
    else:
        print("Usage: python final_force_download.py <URL> [filename]")
