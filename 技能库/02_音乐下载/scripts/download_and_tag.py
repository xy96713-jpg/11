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
from mutagen.id3 import ID3, APIC
from PIL import Image

def clean_filename(text):
    # 简单的文件名清理，去除非法字符
    return re.sub(r'[\\/*?:"<>|]', "", text).strip().replace(" ", "_")
def download_and_search(query, filename=None, video_id=None):
    # [V8.3] 绝对路径: 仅路由至原始 SoundCloud Agent (Stable Modular Core)
    # 彻底废弃旧版 sc_downloader.py，确保逻辑单一
    if "soundcloud.com" in query and (query.startswith("http") or "scsearch" in query):
        print(f"🔀 识别到 SoundCloud 指令，正在调用核心 Agent (soundcloud_agent.py)...")
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soundcloud_agent.py")
        try:
            # 原始 Agent 接受 url 作为第一个参数
            subprocess.run([sys.executable, script_path, query], check=True)
            return
        except Exception as e:
            print(f"❌ 核心 Agent 调用异常: {e}")
            return # 不再回退，避免混淆，直接报错让用户知晓

    # [SEARCH MODE] 如果不是直连，或者专用脚本失败
    # 清理搜索词，去除 BOM 和多余空格
    query = query.strip().replace("\ufeff", "")
    # [V8.0] 路径标准化: D:\song
    output_dir = r"D:\song"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 如果没有指定文件名，先用 query 占位，稍后用视频标题更新
    safe_name = filename if filename else clean_filename(query)
    
    # [V8.0] 直连优先策略
    # 如果是 URL，直接传递给 yt-dlp，不再强制搜索
    is_direct_url = query.startswith("http")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': True,
        'no_warnings': True,
        # 即使是直连，也保持对 YouTube 的封锁 (除非用户明确要求解禁，但目前策略是 SC 优先)
        'block_extractors': ['youtube', 'youtube:tab', 'youtube:playlist', 'youtube:search'], 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }
    cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
        print(f"🍪 已加载通用 Cookies (支持网易云等): {cookie_path}")

    # 搜索方案构建
    if is_direct_url:
        print(f"🔗 检测到直接链接，启动直连模式...")
        search_variants = [query]
    else:
        # 仅使用 SoundCloud 搜索
        search_variants = [f"scsearch1:{query}"]
    
    success = False
    entry = None
    
    for search_query in search_variants:
        if success: break
        if not is_direct_url:
            print(f"🔍 尝试平台方案: {search_query} ...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # [V8.0] 如果是直连，不要搜索，直接提取
                    info = ydl.extract_info(search_query, download=True)
                except yt_dlp.utils.DownloadError as e:
                    if "403" in str(e) or "Sign in" in str(e) or "Inappropriate" in str(e):
                        print(f"⚠️ 当前平台暂时受限，尝试下一个搜索方案...")
                        continue
                    else:
                        print(f"⚠️ 下载错误: {e}")
                        continue
                
                # 处理 info (如果是 playlist 或 search result，info 是 dict 包含 entries)
                # 如果是直接单曲 URL，info 本身就是 entry
                if 'entries' in info:
                    if not info['entries']: continue
                    entry = info['entries'][0]
                else:
                    entry = info

                video_title = entry.get('title', 'Unknown')
                
                # [V6.1] 硬核匹配校验 (仅针对非直连搜索)
                if not is_direct_url:
                    keywords = [k.lower() for k in re.split(r'[-\s]', query) if len(k) > 1]
                    title_lower = video_title.lower()
                    if not any(kw in title_lower for kw in keywords):
                        print(f"⚠️ 校验失败: 资源标题 '{video_title}' 与搜索词 '{query}' 匹配度过低，跳过。")
                        continue
                
                print(f"✅ 锁定资源: {video_title} (来自 {entry.get('extractor', '未知')})")
                success = True

                # --- 智能文件定位与处理 ---
                import time
                time.sleep(2) 
                
                # 重新定位最新下载的文件
                list_of_files = list(Path(output_dir).glob('*.mp3'))
                if not list_of_files:
                    print("❌ 错误：未能在目录中找到下载的音频文件。")
                    return
                
                downloaded_mp3_path = max(list_of_files, key=os.path.getmtime)
                
                # 重命名逻辑
                final_name = filename if filename else clean_filename(video_title)
                final_mp3_path = Path(output_dir) / f"{final_name}.mp3"

                if downloaded_mp3_path.resolve() != final_mp3_path.resolve():
                    if final_mp3_path.exists():
                        try:
                            os.remove(final_mp3_path)
                        except OSError: pass
                    try:
                        os.rename(downloaded_mp3_path, final_mp3_path)
                    except OSError as e:
                        print(f"⚠️ 重命名受阻: {e}")
                        final_mp3_path = downloaded_mp3_path
                break 
                
        except Exception as e:
            print(f"❌ 方案异常: {e}")
            continue

    if not success or not entry:
        print("❌ 所有搜索方案均未成功，请检查网络或 Cookies。")
        return

    # [V8.0] 智能 iTunes 封面搜索 (支持递归关键词清理)
    def get_itunes_metadata(artist_arg, title_arg):
        # 定义需要剥离的关键词
        replacements = ["(Ferraz edit)", "(Fadille Edit)", "Edit", "Remix", "Bootleg", "(Visualizer)", "Official", "Audio", "Lyrics", "Video", "MV", "Full", "Topic", "1080p", "720p"]
        
        queries = []
        # 1. 原始组合 (仅清理特殊符号)
        term1 = f"{artist_arg} {title_arg}"
        queries.append(term1)

        # 2. 深度清理 (剥离 Remix 等)
        term2 = term1
        for r in replacements:
            term2 = re.sub(re.escape(r), "", term2, flags=re.IGNORECASE)
        queries.append(term2.strip())
        
        # 3. 仅标题 (如果包含 - )
        if "-" in title_arg:
            queries.append(f"{artist_arg} {title_arg.split('-')[0]}")
        
        # 4. 简单组合
        queries.append(f"{artist_arg} {title_arg}")
        
        # 去重并搜索
        seen = set()
        for q in queries:
            q_clean = re.sub(r'\s+', ' ', q).strip()
            if not q_clean or q_clean in seen: continue
            seen.add(q_clean)
            
            print(f"🎨 [iTunes] 尝试搜索: '{q_clean}'...")
            try:
                url = "https://itunes.apple.com/search"
                params = {"term": q_clean, "media": "music", "entity": "song", "limit": 1}
                resp = requests.get(url, params=params, timeout=5)
                data = resp.json()
                
                if data["resultCount"] > 0:
                    result = data["results"][0]
                    print(f" -> ✅ 找到官方元数据: {result.get('trackName')} - {result.get('artistName')}")
                    return {
                        "url": result["artworkUrl100"].replace("100x100bb", "1000x1000bb"),
                        "album": result.get("collectionName", "Unknown Album"),
                        "artist": result.get("artistName", "Unknown Artist"),
                        "title": result.get("trackName", "Unknown Title")
                    }
            except Exception: pass
        return None

    # [V7.1] MusicBrainz Cover Art Archive 封面获取 (iTunes 失败时的备选)
    def get_musicbrainz_cover(search_term):
        """从 MusicBrainz/Cover Art Archive 获取高清封面"""
        try:
            import musicbrainzngs
            musicbrainzngs.set_useragent("AntigravityMusicExpert", "7.1", "https://github.com")
            
            clean_term = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|1080p|720p)', '', search_term).strip()
            print(f"🎨 [MusicBrainz] 尝试搜索: '{clean_term}'...")
            
            result = musicbrainzngs.search_recordings(query=clean_term, limit=1)
            if result['recording-list']:
                recording = result['recording-list'][0]
                if 'release-list' in recording and recording['release-list']:
                    release_id = recording['release-list'][0]['id']
                    try:
                        cover_data = musicbrainzngs.get_image_front(release_id, size="500")
                        if cover_data:
                            print(f"✅ 从 Cover Art Archive 获取到封面")
                            return {"data": cover_data, "type": "binary"}
                    except musicbrainzngs.ResponseError:
                        pass
        except ImportError:
            print("⚠️ musicbrainzngs 未安装，跳过 MusicBrainz 封面搜索")
        except Exception as e:
            pass
        return None


    # --- 封面与标签处理 ---
    print("🎨 正在注入高品质封面与 ID3 标签...")
    
    # 解析文件名或查询词以获取 Artist/Title 用于搜索
    # 优先使用视频标题，因为那是真实的资源
    pass_artist = "Unknown"
    pass_title = video_title
    if " - " in video_title:
        pass_artist, pass_title = video_title.split(" - ", 1)
    
    # 获取元数据
    itunes_data = get_itunes_metadata(pass_artist, pass_title)
    
    # 备选封面
    thumbnails = entry.get('thumbnails', [])
    video_cover_url = thumbnails[-1]['url'] if thumbnails else None
    
    # [V7.1] 多源封面获取策略: iTunes -> MusicBrainz -> Video Thumbnail
    final_cover_url = None
    musicbrainz_cover_data = None
    
    if itunes_data and itunes_data.get("url"):
        final_cover_url = itunes_data["url"]
    else:
        # 尝试 MusicBrainz Cover Art Archive
        mb_cover = get_musicbrainz_cover(query)
        if mb_cover and mb_cover.get("type") == "binary":
            musicbrainz_cover_data = mb_cover["data"]
            print("🎨 使用 MusicBrainz/Cover Art Archive 封面")
        elif video_cover_url:
            final_cover_url = video_cover_url
            print("🎨 使用视频缩略图作为封面")

    
    try:
        audio = MP3(str(final_mp3_path), ID3=ID3)
        if audio.tags is None: audio.add_tags()
        
        from mutagen.id3 import TIT2, TPE1, TALB
        if itunes_data:
            audio.tags.add(TIT2(encoding=3, text=itunes_data["title"]))
            audio.tags.add(TPE1(encoding=3, text=itunes_data["artist"]))
            audio.tags.add(TALB(encoding=3, text=itunes_data["album"]))
        else:
            parts = video_title.split(" - ", 1)
            if len(parts) == 2:
                audio.tags.add(TPE1(encoding=3, text=parts[0].strip()))
                audio.tags.add(TIT2(encoding=3, text=parts[1].strip()))
            else:
                audio.tags.add(TIT2(encoding=3, text=video_title))

        # [V7.1] 支持 URL 或二进制封面数据
        cover_embedded = False
        if musicbrainz_cover_data:
            # 直接使用 MusicBrainz 二进制数据
            try:
                img = Image.open(io.BytesIO(musicbrainz_cover_data))
                w, h = img.size
                if w != h:
                    min_dim = min(w, h)
                    left = (w - min_dim) / 2
                    top = (h - min_dim) / 2
                    img = img.crop((left, top, left + min_dim, top + min_dim))
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=95)
                audio.tags.delall("APIC")
                audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_byte_arr.getvalue()))
                cover_embedded = True
            except Exception as e:
                print(f"⚠️ MusicBrainz 封面处理失败: {e}")
        
        if not cover_embedded and final_cover_url:
            resp = requests.get(final_cover_url, timeout=15)
            img = Image.open(io.BytesIO(resp.content))
            
            w, h = img.size
            if w != h:
                min_dim = min(w, h)
                left = (w - min_dim) / 2
                top = (h - min_dim) / 2
                img = img.crop((left, top, left + min_dim, top + min_dim))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95)
            audio.tags.delall("APIC")
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_byte_arr.getvalue()))
            cover_embedded = True
        
        if not cover_embedded:
            print("⚠️ 未能获取到任何封面")

            
        audio.save(v2_version=3)
        print("✅ ID3 标签(v2.3)与高清封面写入成功！")
    except Exception as e:
        print(f"⚠️ 标签写入失败: {e}")

    print(f"\n🎉 完美交付: {final_mp3_path}")
    return 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Music Expert V5.4")
    parser.add_argument("query", help="歌曲搜索词")
    parser.add_argument("--name", help="指定保存的文件名 (可选)", default=None)
    args = parser.parse_args()

    download_and_search(args.query, args.name)
