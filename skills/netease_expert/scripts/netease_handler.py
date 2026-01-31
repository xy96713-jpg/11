import sys
import os
import requests
from pyncm import apis, GetCurrentSession, LoadSessionFromString
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

def load_session():
    if os.path.exists('netease_session.ncm'):
        try:
            with open('netease_session.ncm', 'r') as f:
                LoadSessionFromString(f.read())
            # Verify login
            sess = GetCurrentSession()
            if sess.login_info['success']:
                print(f"Logged in as: {sess.login_info['content']['profile']['nickname']}")
            else:
                print("Session loaded but login invalid.")
        except Exception as e:
            print(f"Failed to load session: {e}")

def download_by_id(song_id, output_dir):
    print(f"Resolving Song ID: {song_id}")
    
    # 1. Get Track Details
    track_info = apis.track.GetTrackDetail(song_id)
    if not track_info.get('songs'):
        print("Track not found.")
        return
        
    song = track_info['songs'][0]
    title = song['name']
    artist = song['ar'][0]['name']
    album = song['al']['name']
    cover_url = song['al']['picUrl']
    
    print(f"Found: {title} - {artist} ({album})")
    
    # 2. Get Audio URL
    # Try high quality first, then fallback
    bitrates = [320000, 128000] 
    audio_info = None
    
    for br in bitrates:
        print(f"Trying bitrate: {br}...")
        res = apis.track.GetTrackAudio(song_id, bitrate=br)
        if res.get('data') and res['data'][0]['url']:
            audio_info = res
            print(f"Got URL at {br}bps")
            break
            
    if not audio_info or not audio_info.get('data') or not audio_info['data'][0]['url']:
        print("No audio data returned (All bitrates failed).")
        return

    data = audio_info['data'][0]
    mp3_url = data['url']
    if not mp3_url:
        print("URL is empty. Requires VIP/Login or song is blocked.")
        return
        
    # 3. Download
    filename = f"{artist} - {title}.mp3".replace("/", "_").replace("\\", "_")
    output_path = os.path.join(output_dir, filename)
    
    print(f"Downloading from {mp3_url}...")
    with requests.get(mp3_url, stream=True) as r:
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
    # 4. Tagging
    print("Applying metadata...")
    try:
        audio = MP3(output_path, ID3=ID3)
        if audio.tags is None: audio.add_tags()
        
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TALB(encoding=3, text=album))
        
        if cover_url:
            img_data = requests.get(cover_url).content
            audio.tags.add(APIC(
                encoding=3, 
                mime='image/jpeg', 
                type=3, 
                desc='Cover', 
                data=img_data
            ))
        
        audio.save(v2_version=3)
        print(f"Success: {output_path}")
    except Exception as e:
        print(f"Tagging error: {e}")

def search_song(keyword):
    print(f"Searching for: {keyword}")
    res = apis.cloudsearch.GetSearchResult(keyword, stype=1, limit=5)
    if not res.get('result') or not res['result'].get('songs'):
        print("No results found.")
        return

    print(f"\nSearch Results for '{keyword}':")
    print("-" * 50)
    for song in res['result']['songs']:
        print(f"ID: {song['id']} | {song['name']} - {song['ar'][0]['name']} ({song['al']['name']})")
    print("-" * 50)

if __name__ == "__main__":
    load_session()
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python netease_handler.py search [KEYWORD]")
        print("  python netease_handler.py download [SONG_ID]")
        sys.exit(1)
        
    mode = sys.argv[1]
    arg = sys.argv[2]
    
    if mode == 'search':
        search_song(arg)
    elif mode == 'download':
        output = r"D:\song\Netease_Downloads"
        if not os.path.exists(output):
            os.makedirs(output)
        download_by_id(arg, output)
    else:
        print("Invalid mode. Use 'search' or 'download'.")
