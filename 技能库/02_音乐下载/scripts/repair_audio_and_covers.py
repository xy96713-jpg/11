import os
import glob
import subprocess
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import requests
import io
from PIL import Image

TARGET_DIR = r"D:\song"
FFMPEG_CMD = "ffmpeg"

def convert_m4a_to_mp3():
    files = glob.glob(os.path.join(TARGET_DIR, "*.m4a"))
    print(f"Found {len(files)} M4A files to convert.")
    
    for m4a_path in files:
        mp3_path = m4a_path.replace(".m4a", ".mp3")
        print(f"Converting: {os.path.basename(m4a_path)} -> MP3...")
        
        # FFmpeg conversion
        try:
            cmd = [FFMPEG_CMD, "-i", m4a_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path, "-y", "-hide_banner", "-loglevel", "error"]
            subprocess.run(cmd, check=True)
            
            # If successful, delete m4a
            os.remove(m4a_path)
            print(" - Conversion success. M4A deleted.")
        except Exception as e:
            print(f" - Conversion failed: {e}")

def fix_metadata(filename_keyword, correct_artist, correct_title, album_override=None):
    # Find list of mp3s matching keyword
    files = glob.glob(os.path.join(TARGET_DIR, "*.mp3"))
    target_files = [f for f in files if filename_keyword.lower() in os.path.basename(f).lower()]
    
    for f_path in target_files:
        print(f"Fixing Tags for: {os.path.basename(f_path)}")
        try:
            audio = MP3(f_path, ID3=ID3)
            if audio.tags is None: audio.add_tags()
            
            audio.tags.add(TPE1(encoding=3, text=correct_artist))
            audio.tags.add(TIT2(encoding=3, text=correct_title))
            if album_override:
                audio.tags.add(TALB(encoding=3, text=album_override))
            
            # Clean existing covers (Purge DMX/Wrong covers)
            audio.tags.delall("APIC")
            
            # Search Cover
            queries = [f"{correct_artist} {correct_title}", correct_title]
            if "Only cry in the rain" in correct_title:
                queries = ["The Escape of the Seven Only cry in the rain", "Only cry in the rain"]

            cover_url = None
            for q in queries:
                print(f" - Searching iTunes for: {q}")
                try:
                    url = "https://itunes.apple.com/search"
                    params = {"term": q, "media": "music", "entity": "song", "limit": 1}
                    resp = requests.get(url, params=params, timeout=5)
                    data = resp.json()
                    
                    if data['resultCount'] > 0:
                        print(" - Found iTunes Cover!")
                        cover_url = data['results'][0]['artworkUrl100'].replace('100x100bb', '1000x1000bb')
                        break
                except: pass
            
            if cover_url:
                img_data = requests.get(cover_url).content
                img = Image.open(io.BytesIO(img_data))
                if img.mode != 'RGB': img = img.convert('RGB')
                out_io = io.BytesIO()
                img.save(out_io, format='JPEG', quality=95)
                
                audio.tags.delall("APIC")
                audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=out_io.getvalue()))
            
            audio.save()
            print(" - Tags updated.")
            
        except Exception as e:
            print(f" - Error fixing tags: {e}")

if __name__ == "__main__":
    # 1. Convert all M4A to MP3
    convert_m4a_to_mp3()
    
    # 2. Fix specific tracks complained by user
    # "Chuu - Only cry in the rain" -> Found inconsistent cover (DMX)
    fix_metadata("Only_cry_in_the_rain", "Chuu", "Only cry in the rain - OST", "Recorner Vol.3") # Try exact guess or just let search find it
    
    # "Destiny's Child - Lose My Breath"
    fix_metadata("Lose_My_Breath", "Destiny's Child", "Lose My Breath")

    # "Something New" (Fadille Edit)
    fix_metadata("Something New", "Zendaya", "Something New", "Something New (feat. Chris Brown) - Single")
    
    # "Destiny's Child - Bootylicious" (Ferraz Edit)
    fix_metadata("Bootylicious", "Destiny's Child", "Bootylicious")
