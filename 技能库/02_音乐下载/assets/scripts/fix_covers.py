import os
import requests
import io
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image

def get_itunes_cover(query):
    """从 iTunes 获取高清封面 (1000x1000)"""
    print(f"🔍 正在从 iTunes 搜索: {query}...")
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['resultCount'] > 0:
            result = data['results'][0]
            cover_url = result['artworkUrl100'].replace('100x100bb.jpg', '1000x1000bb.jpg')
            return cover_url
    except Exception as e:
        print(f"❌ iTunes 搜索失败: {e}")
    return None

def embed_cover_v54(mp3_path, cover_url):
    """【V5.4 工业级标准修复】对标 Windows 预览机制"""
    try:
        print(f"📥 正在处理封面: {cover_url}")
        resp = requests.get(cover_url, timeout=15)
        img = Image.open(io.BytesIO(resp.content))
        
        # 强制 1:1 居中裁剪
        w, h = img.size
        if w != h:
            min_dim = min(w, h)
            left = (w - min_dim) / 2
            top = (h - min_dim) / 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        
        # 彻底清洗旧标签
        id3 = ID3(mp3_path)
        id3.delete()
        
        # 强制 v2.3 + Desc='Cover'
        id3 = ID3()
        id3.add(APIC(
            encoding=3,
            mime='image/jpeg',
            type=3, # Front cover
            desc='Cover', 
            data=buf.getvalue()
        ))
        id3.save(mp3_path, v2_version=3)
        
        # 触发物理属性刷新
        temp = mp3_path + ".v54"
        os.rename(mp3_path, temp)
        os.rename(temp, mp3_path)
        
        print(f"✅ V5.4 标准修复成功: {os.path.basename(mp3_path)}")
        return True
    except Exception as e:
        print(f"❌ 修复失败: {e}")
    return False

def fix_directory(directory, custom_files=None):
    if custom_files:
        files_to_fix = custom_files
    else:
        # 默认修复已知易错文件
        files_to_fix = {
            'aespa_Angel_48.mp3': 'aespa Angel',
            '82MAJOR_Need_That_Bass_Test.mp3': '82MAJOR Need That Bass',
            'Bicycle Ride (Soca Remix).mp3': 'Vybz Kartel Bicycle Ride Soca Remix',
            'Delulu.mp3': 'Delulu song'
        }
    
    for filename, query in files_to_fix.items():
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            cover_url = get_itunes_cover(query)
            if cover_url:
                embed_cover_v54(path, cover_url)
        else:
            print(f"⚠️ 跳过不存在的文件: {filename}")

if __name__ == "__main__":
    fix_directory(r"D:\song\Final_Music_Official")
