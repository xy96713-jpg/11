import os
import re
import glob
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC
import requests
import io
from PIL import Image

TARGET_DIR = r"D:\song"

def search_cover(artist, title):
    # Cleaning Logic
    replacements = ["(Ferraz edit)", "(Fadille Edit)", "Edit", "Remix", "Bootleg", "(Visualizer)", "Official"]
    
    queries = []
    # 1. Full cleaned string
    term1 = f"{artist} {title}"
    for r in replacements:
        term1 = re.sub(re.escape(r), "", term1, flags=re.IGNORECASE)
    queries.append(term1.strip())
    
    # 2. Key parts
    if "-" in title:
        queries.append(f"{artist} {title.split('-')[0]}")
    
    # 3. Simple Artist + Title
    queries.append(f"{artist} {title}")
    
    for q in queries:
        print(f"Searching iTunes for: {q}")
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": q, "media": "music", "entity": "song", "limit": 1}
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data['resultCount'] > 0:
                print(f" -> Found match!")
                return data['results'][0]['artworkUrl100'].replace('100x100bb', '1000x1000bb')
        except:
            pass
    return None

def fix_m4a(path):
    print(f"Scanning: {os.path.basename(path)}")
    try:
        audio = MP4(path)
        
        # Check if cover exists
        if 'covr' in audio:
            print(" - Cover already exists.")
            # return # User said they didn't see it, maybe incompatible format? Let's overwrite to be sure if script is forced.
            # But let's assume if it's there, it might be the yt-dlp webp thumbnail which windows hates.
        
        artist = audio.tags.get('©ART', [''])[0]
        title = audio.tags.get('©nam', [''])[0]
        
        if not artist or not title:
            # Fallback to filename
            name = os.path.splitext(os.path.basename(path))[0]
            if " - " in name:
                artist, title = name.split(" - ", 1)
            else:
                artist = "Unknown"
                title = name
        
        # Search Cover
        cover_url = search_cover(artist, title)
        if not cover_url:
            print(" - No cover found online.")
            return

        print(f" - Found Cover: {cover_url}")
        img_data = requests.get(cover_url).content
        
        # Convert to JPEG for maximum compatibility
        img = Image.open(io.BytesIO(img_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        out_io = io.BytesIO()
        img.save(out_io, format='JPEG', quality=90)
        
        audio['covr'] = [MP4Cover(out_io.getvalue(), imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()
        print(" - Cover embedded (JPEG).")
        
    except Exception as e:
        print(f"Error processing {path}: {e}")

# Scan
files = glob.glob(os.path.join(TARGET_DIR, "*.m4a"))
for f in files:
    fix_m4a(f)
