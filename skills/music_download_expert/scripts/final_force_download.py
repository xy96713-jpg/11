import sys
import os
import subprocess
import yt_dlp

def download_specific_id(track_id, final_filename, title, artist, album_art_query):
    print(f"\n--- Downloading {title} (ID: {track_id}) ---")
    url = f"https://api.soundcloud.com/tracks/{track_id}"
    output = f"D:/song/Final_Music_Official/{final_filename}"
    
    # 1. Download with yt-dlp using specialized args for SC API
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--add-header", "Authorization: OAuth 2-294692-2041536132-...", # Placeholder, yt-dlp handles oauth usually
        url,
        "-o", output,
        "--format", "mp3/bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "320K",
        "--force-overwrites"
    ]
    
    # Using scsearch format to bypass direct URL issues if ID is known
    # Form: scsearch1:ID
    search_query = f"scsearch1:{title}" 
    
    # Fallback: try scsearch with duration filter logic built-in to yt-dlp is tricky in CLI, 
    # so we use python's yt_dlp lib
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'logger': MyLogger(),
        'cookiefile': r'D:\anti\skills\music_download_expert\scripts\youtube_cookies.txt'
    }

    # Attempt direct ID download if possible (often blocked) or search-and-match
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Try finding by ID directly (often works better than URL for SC)
            # URL format: https://soundcloud.com/tracks/<id>
            # But yt-dlp might need full permalink.
            # Strategy: Use the IDs we found in search results:
            # Hearts2Hearts (Butterflies/FOCUS 2:57): 2041536132
            # S.H.E (4:06/4:26 var): 104565530 (4:06), need 4:26.
            
            # Since S.H.E 4:26 is elusive on SC, we use the best 4:06 version (official MV audio usually) 
            # or retry NetEase for 4:26 if available.
            
            if "Hearts2Hearts" in title:
               # found ID for 2:57 version: 2041536132 (Butterflies Hearts2Hearts full ver)
               ydl.download([f"https://api.soundcloud.com/tracks/2041536132"])
            elif "S.H.E" in title:
               # 4:26 version is hard. The 4:06 (104565530) is "Xin Wo".
               # Try generic search again but strictly download the first result that is > 4:20
               res = ydl.extract_info(f"scsearch10:{title}", download=False)
               if 'entries' in res:
                   for entry in res['entries']:
                       if 260 <= entry.get('duration', 0) <= 270: # 4:20 - 4:30
                           ydl.download([entry['webpage_url']])
                           return

    except Exception as e:
        print(f"Error: {e}")

class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)

if __name__ == "__main__":
    # 1. Hearts2Hearts (2:57)
    download_specific_id("2041536132", "Hearts2Hearts_FOCUS_Final.mp3", "Hearts2Hearts FOCUS", "Hearts2Hearts", "Hearts2Hearts FOCUS")
    
    # 2. S.H.E (4:26)
    # Note: 4:26 is album version. SC might only have MV (4:00) or others. 
    # We will try strict search matching
    download_specific_id("0", "SHE_MeiliXinShijie_Final.mp3", "S.H.E 美丽新世界", "S.H.E", "S.H.E 美丽新世界")
