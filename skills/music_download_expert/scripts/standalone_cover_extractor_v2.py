import os
import requests
import re
import io
from PIL import Image
import time

def get_itunes_cover(search_term, output_path):
    """从 iTunes 获取高清封面并保存"""
    clean_term = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|1080p|720p)', '', search_term).strip()
    clean_term = re.sub(r'\s+', ' ', clean_term)
    
    print(f"🔍 搜索: {clean_term}")
    for attempt in range(3):
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": clean_term, "media": "music", "entity": "song", "limit": 1}
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            
            if data["resultCount"] > 0:
                result = data["results"][0]
                cover_url = result["artworkUrl100"].replace("100x100bb", "1000x1000bb")
                print(f"✅ 找到封面: {cover_url}")
                
                img_resp = requests.get(cover_url, timeout=20)
                img = Image.open(io.BytesIO(img_resp.content))
                
                w, h = img.size
                if w != h:
                    min_dim = min(w, h)
                    left = (w - min_dim) / 2
                    top = (h - min_dim) / 2
                    img = img.crop((left, top, left + min_dim, top + min_dim))
                
                img.convert('RGB').save(output_path, 'JPEG', quality=95)
                print(f"💾 已保存到: {output_path}")
                return True
            else:
                print(f"❌ 未找到封面: {clean_term}")
                return False
        except Exception as e:
            print(f"⚠️ 尝试 {attempt+1} 失败: {e}")
            time.sleep(2)
    return False

if __name__ == "__main__":
    output_dir = r"D:\视频文件\视频图片"
    
    songs = [
        ("Daz Dillinger - In California", "In California.jpg"),
        ("Utada Hikaru - Distance (M-Flo Remix)", "Distance (M-Flo Remix).jpg"),
        ("XG - HYPNOTIZE", "HYPNOTIZE.jpg")
    ]
    
    for query, filename in songs:
        target_path = os.path.join(output_dir, filename)
        if not os.path.exists(target_path):
            get_itunes_cover(query, target_path)
        else:
            print(f"⏭️ 跳过已存在的文件: {filename}")
