import os
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

def get_itunes_metadata(query):
    print(f"Searching iTunes: {query}")
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
        print(f"iTunes error: {e}")
    return None

def apply_metadata_robust(path, meta):
    try:
        # Load or create tags
        try:
            audio = ID3(path)
        except:
            audio = ID3()
        
        # Clear existing tags to be safe
        audio.delete()
        
        # Add basic info
        audio.add(TIT2(encoding=3, text=meta['title']))
        audio.add(TPE1(encoding=3, text=meta['artist']))
        audio.add(TALB(encoding=3, text=meta['album']))
        
        # Add APIC (Cover)
        if meta.get('cover'):
            print(f"Downloading cover: {meta['cover']}")
            img_data = requests.get(meta['cover'], timeout=10).content
            audio.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3, # Front cover
                desc='Cover',
                data=img_data
            ))
        
        # Save as v2.3 for Windows compatibility
        audio.save(path, v2_version=3)
        print(f"SUCCESS (v2.3): {os.path.basename(path)}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        path_arg = sys.argv[1]
        query_arg = sys.argv[2]
        
        # If path is only filename, join with D:\song
        if not os.path.isabs(path_arg):
            path_arg = os.path.join(r"D:\song", path_arg)
            
        if os.path.exists(path_arg):
            meta = get_itunes_metadata(query_arg)
            if meta:
                apply_metadata_robust(path_arg, meta)
            else:
                print(f"⚠️ Could not find metadata for: {query_arg}")
        else:
            print(f"❌ File not found: {path_arg}")
    else:
        print("Usage: python robust_tagger.py <filepath> <search_query>")
