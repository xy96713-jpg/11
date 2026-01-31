import os
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

def get_itunes_metadata(query):
    print(f"Searching iTunes for: {query}...")
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['resultCount'] > 0:
            res = data['results'][0]
            cover = res['artworkUrl100'].replace('100x100bb.jpg', '1000x1000bb.jpg')
            return {
                'title': res['trackName'],
                'artist': res['artistName'],
                'album': res['collectionName'],
                'cover': cover
            }
    except Exception as e:
        print(f"Error: {e}")
    return None

def apply_metadata(path, meta):
    try:
        audio = MP3(path, ID3=ID3)
        if audio.tags is None: audio.add_tags()
        audio.tags.delall('APIC')
        audio.tags.add(TIT2(encoding=3, text=meta['title']))
        audio.tags.add(TPE1(encoding=3, text=meta['artist']))
        audio.tags.add(TALB(encoding=3, text=meta['album']))
        
        if meta.get('cover'):
            img_data = requests.get(meta['cover']).content
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_data))
        
        audio.save(v2_version=3)
        print(f"SUCCESS: {os.path.basename(path)}")
    except Exception as e:
        print(f"FAIL {path}: {e}")

def main():
    dir_path = r"D:\song\Final_Music_Official"
    mapping = {
        "aespa_Angel_48.mp3": "aespa Angel #48",
        "Hearts2Hearts_FOCUS.mp3": "Hearts2Hearts FOCUS 2:57",
        "SHE_MeiliXinShijie_Official.mp3": "S.H.E 美丽新世界",
        "TTS_Stay.mp3": "TaeTiSeo Stay Holler"
    }
    for f, q in mapping.items():
        path = os.path.join(dir_path, f)
        if os.path.exists(path):
            meta = get_itunes_metadata(q)
            if meta: apply_metadata(path, meta)

if __name__ == "__main__":
    main()
