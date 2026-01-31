"""
修复缺失封面的脚本 - 针对 Delulu.mp3 和 High Ku
"""
import os
import sys
import io
import re
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from PIL import Image

def get_itunes_cover(search_term):
    """从 iTunes 获取封面"""
    clean_term = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|1080p|720p|campus club|chinese man)', '', search_term).strip()
    clean_term = re.sub(r'\s+', ' ', clean_term)
    print(f"🎨 从 iTunes 搜索封面: '{clean_term}'...")
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": clean_term, "media": "music", "entity": "song", "limit": 3}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data["resultCount"] > 0:
            for result in data["results"]:
                cover_url = result["artworkUrl100"].replace("100x100bb", "1000x1000bb")
                return {
                    "url": cover_url,
                    "artist": result.get("artistName", "Unknown"),
                    "title": result.get("trackName", "Unknown"),
                    "album": result.get("collectionName", "Unknown")
                }
    except Exception as e:
        print(f"iTunes 搜索失败: {e}")
    return None

def get_musicbrainz_cover(search_term):
    """从 MusicBrainz/Cover Art Archive 获取封面"""
    try:
        import musicbrainzngs
        musicbrainzngs.set_useragent("AntigravityFixCovers", "1.0", "https://github.com")
        clean_term = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|campus club|chinese man)', '', search_term).strip()
        print(f"🎨 从 MusicBrainz 搜索封面: '{clean_term}'...")
        result = musicbrainzngs.search_recordings(query=clean_term, limit=3)
        if result['recording-list']:
            for recording in result['recording-list']:
                if 'release-list' in recording and recording['release-list']:
                    release_id = recording['release-list'][0]['id']
                    try:
                        cover_data = musicbrainzngs.get_image_front(release_id, size="500")
                        if cover_data:
                            return {"data": cover_data, "type": "binary"}
                    except:
                        continue
    except Exception as e:
        print(f"MusicBrainz 搜索失败: {e}")
    return None

def embed_cover(mp3_path, search_term):
    """为 MP3 文件嵌入封面"""
    print(f"\n处理: {os.path.basename(mp3_path)}")
    
    # 尝试 iTunes
    itunes = get_itunes_cover(search_term)
    
    if itunes and itunes.get("url"):
        print(f"✅ 从 iTunes 获取到封面")
        try:
            resp = requests.get(itunes["url"], timeout=15)
            img = Image.open(io.BytesIO(resp.content))
            
            # 裁剪为正方形
            w, h = img.size
            if w != h:
                min_dim = min(w, h)
                left = (w - min_dim) / 2
                top = (h - min_dim) / 2
                img = img.crop((left, top, left + min_dim, top + min_dim))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95)
            
            audio = MP3(mp3_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            audio.tags.delall("APIC")
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_byte_arr.getvalue()))
            
            # 更新元数据
            audio.tags.add(TIT2(encoding=3, text=itunes["title"]))
            audio.tags.add(TPE1(encoding=3, text=itunes["artist"]))
            audio.tags.add(TALB(encoding=3, text=itunes["album"]))
            
            audio.save(v2_version=3)
            print(f"✅ 封面和标签已写入: {os.path.basename(mp3_path)}")
            return True
        except Exception as e:
            print(f"⚠️ iTunes 封面处理失败: {e}")
    
    # 尝试 MusicBrainz
    mb = get_musicbrainz_cover(search_term)
    if mb and mb.get("type") == "binary":
        print(f"✅ 从 MusicBrainz 获取到封面")
        try:
            img = Image.open(io.BytesIO(mb["data"]))
            w, h = img.size
            if w != h:
                min_dim = min(w, h)
                left = (w - min_dim) / 2
                top = (h - min_dim) / 2
                img = img.crop((left, top, left + min_dim, top + min_dim))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95)
            
            audio = MP3(mp3_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            audio.tags.delall("APIC")
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_byte_arr.getvalue()))
            audio.save(v2_version=3)
            print(f"✅ MusicBrainz 封面已写入: {os.path.basename(mp3_path)}")
            return True
        except Exception as e:
            print(f"⚠️ MusicBrainz 封面处理失败: {e}")
    
    print(f"❌ 未能找到封面")
    return False

if __name__ == "__main__":
    output_dir = r"D:\song\Final_Music_Official"
    
    # 需要修复的文件
    files_to_fix = [
        ("Delulu.mp3", "KiiiKiii Delulu"),
        ("High Ku ｜ Campus Club x Chinese Man.mp3", "High Ku Campus Club Chinese Man"),
    ]
    
    for filename, search_term in files_to_fix:
        mp3_path = os.path.join(output_dir, filename)
        if os.path.exists(mp3_path):
            embed_cover(mp3_path, search_term)
        else:
            print(f"⚠️ 文件不存在: {filename}")
    
    print("\n✅ 封面修复完成!")
