import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

def check_files(directory):
    print(f"{'Filename':<40} | {'Title':<30} | {'Artist':<20} | {'Len':<5}")
    print("-" * 100)
    for f in os.listdir(directory):
        if not f.endswith('.mp3'): continue
        path = os.path.join(directory, f)
        try:
            audio = MP3(path)
            title = audio.tags.get('TIT2', 'None')
            artist = audio.tags.get('TPE1', 'None')
            duration = int(audio.info.length)
            print(f"{f[:40]:<40} | {str(title)[:30]:<30} | {str(artist)[:20]:<20} | {duration}s")
        except Exception as e:
            print(f"{f[:40]:<40} | Error reading: {e}")

if __name__ == "__main__":
    check_files(r"D:\song\Final_Music_Official")
