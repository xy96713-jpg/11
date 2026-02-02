import yt_dlp
import sys
import subprocess
import os
import argparse
import requests
import io
import re
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from PIL import Image

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).strip().replace(" ", "_")

def get_itunes_metadata(artist_arg, title_arg):
    replacements = ["(Ferraz edit)", "(Fadille Edit)", "Edit", "Remix", "Bootleg", "(Visualizer)", "Official", "Audio", "Lyrics", "Video", "MV", "Full", "Topic", "1080p", "720p", "Mastering", "Hi-Res"]
    queries = [f"{artist_arg} {title_arg}"]
    term2 = queries[0]
    for r in replacements:
        term2 = re.sub(re.escape(r), "", term2, flags=re.IGNORECASE)
    term2 = re.sub(r'\(.*?\)', '', term2)
    term2 = re.sub(r'\[.*?\]', '', term2)
    queries.append(term2.strip())
    if "-" in title_arg: queries.append(f"{artist_arg} {title_arg.split('-')[0]}")
    
    seen = set()
    for q in queries:
        q_clean = re.sub(r'\s+', ' ', q).strip()
        if not q_clean or q_clean in seen: continue
        seen.add(q_clean)
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": q_clean, "media": "music", "entity": "song", "limit": 1}
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data["resultCount"] > 0:
                result = data["results"][0]
                return {
                    "url": result["artworkUrl100"].replace("100x100bb", "1000x1000bb"),
                    "album": result.get("collectionName", "Unknown Album"),
                    "artist": result.get("artistName", "Unknown Artist"),
                    "title": result.get("trackName", "Unknown Title")
                }
        except Exception: pass
    return None

def get_musicbrainz_cover(search_term):
    try:
        import musicbrainzngs
        musicbrainzngs.set_useragent("AntigravityMusicExpert", "8.8", "https://github.com")
        clean_term = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|1080p|720p)', '', search_term).strip()
        result = musicbrainzngs.search_recordings(query=clean_term, limit=1)
        if result['recording-list']:
            recording = result['recording-list'][0]
            if 'release-list' in recording and recording['release-list']:
                release_id = recording['release-list'][0]['id']
                try:
                    cover_data = musicbrainzngs.get_image_front(release_id, size="500")
                    if cover_data: return {"data": cover_data, "type": "binary"}
                except Exception: pass
    except Exception: pass
    return None

def _execute_search(query, filename=None, force_direct=False):
    output_dir = r"D:\song"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    is_direct_url = query.startswith("http")
    
    if is_direct_url or force_direct:
        search_variants = [query]
    else:
        print(f"🌊 Waterfall 搜索 (V8.8)...")
        search_variants = [f"scsearch1:{query}", f"bcsearch1:{query}", f"https://music.163.com/#/search/m/?s={query}&type=1"]
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
        'quiet': True,
        'no_warnings': True,
        'block_extractors': ['youtube', 'youtube:tab', 'youtube:playlist', 'youtube:search'], 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }
    cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
    if os.path.exists(cookie_path): ydl_opts['cookiefile'] = cookie_path

    success = False
    entry = None

    for search_query in search_variants:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                entry = info['entries'][0] if 'entries' in info else info
                video_title = entry.get('title', 'Unknown')
                print(f"✅ 锁定资源: {video_title}")
                
                import time
                time.sleep(2)
                list_of_files = list(Path(output_dir).glob('*.mp3'))
                downloaded_mp3_path = max(list_of_files, key=os.path.getmtime)
                
                final_name = filename if filename else clean_filename(video_title)
                final_mp3_path = Path(output_dir) / f"{final_name}.mp3"
                if downloaded_mp3_path.resolve() != final_mp3_path.resolve():
                    if final_mp3_path.exists(): os.remove(final_mp3_path)
                    os.rename(downloaded_mp3_path, final_mp3_path)
                
                # 开始打标签
                _apply_tags(final_mp3_path, entry, query)
                success = True
                break
        except Exception as e:
            print(f"⚠️ 方案失败: {e}")
            continue
    if not success: print("❌ 所有方案均未成功。")

def _apply_tags(mp3_path, entry, query):
    print(f"🎨 正在注入高品质封面与 ID3 标签...")
    video_title = entry.get('title', 'Unknown')
    pass_artist, pass_title = "Unknown", video_title
    if " - " in query and not query.startswith("http"):
        parts = query.split(" - ", 1)
        pass_artist, pass_title = parts[0].strip(), parts[1].strip()
    elif " - " in video_title:
        pass_artist, pass_title = video_title.split(" - ", 1)

    itunes_data = get_itunes_metadata(pass_artist, pass_title)
    
    try:
        audio = MP3(str(mp3_path), ID3=ID3)
        if audio.tags is None: audio.add_tags()
        if itunes_data:
            audio.tags.add(TIT2(encoding=3, text=itunes_data["title"]))
            audio.tags.add(TPE1(encoding=3, text=itunes_data["artist"]))
            audio.tags.add(TALB(encoding=3, text=itunes_data["album"]))
        else:
            audio.tags.add(TIT2(encoding=3, text=pass_title))
            audio.tags.add(TPE1(encoding=3, text=pass_artist))

        # 封面处理
        cover_data = None
        if itunes_data:
            cover_data = requests.get(itunes_data["url"], timeout=10).content
        else:
            mb = get_musicbrainz_cover(pass_title)
            if mb: cover_data = mb["data"]
            elif entry.get('thumbnails'):
                cover_data = requests.get(entry['thumbnails'][-1]['url'], timeout=10).content

        if cover_data:
            img = Image.open(io.BytesIO(cover_data))
            w, h = img.size
            if w != h:
                min_dim = min(w, h)
                img = img.crop(((w-min_dim)/2, (h-min_dim)/2, (w+min_dim)/2, (h+min_dim)/2))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95)
            audio.tags.delall("APIC")
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_byte_arr.getvalue()))
        
        audio.tags.version = (2, 3, 0)
        audio.save(v2_version=3)
        print("✅ 标签注入成功")
    except Exception as e:
        print(f"⚠️ 标签失败: {e}")

def download_and_search(query, filename=None):
    if "soundcloud.com" in query and (query.startswith("http") or "scsearch" in query):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soundcloud_agent.py")
        subprocess.run([sys.executable, script_path, query])
        return

    if "open.spotify.com" in query:
        print(f"🔀 智能桥接 Spotify...")
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(query, headers=headers, timeout=5)
            title_match = re.search(r'<title>(.*?)</title>', resp.text)
            raw_title = ""
            if title_match and "Page not found" not in title_match.group(1):
                raw_title = title_match.group(1).replace(" | Spotify", "").replace(" - song by ", " ").replace("Spotify – ", "").strip()
            if not raw_title:
                og = re.search(r'property="og:title" content="(.*?)"', resp.text)
                if og: raw_title = og.group(1)
            
            if raw_title and "Page not found" not in raw_title:
                print(f"🎯 识别: {raw_title}")
                return _execute_search(raw_title, filename)
            else:
                return _execute_search(query, filename, force_direct=True)
        except Exception:
            return _execute_search(query, filename, force_direct=True)
    
    return _execute_search(query, filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()
    download_and_search(args.query, args.name)
