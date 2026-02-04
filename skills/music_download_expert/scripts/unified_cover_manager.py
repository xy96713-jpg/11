import os
import re
import requests
import io
from PIL import Image
from pathlib import Path

# 配置
LOCAL_COVER_DIR = r"D:\视频文件\视频图片"
ITUNES_API_URL = "https://itunes.apple.com/search"

def clean_term(text):
    """清理搜索关键词"""
    # 去除常见后缀
    text = re.sub(r'(?i)(audio|official|lyrics|video|mv|full|topic|1080p|720p)', '', text)
    # 去除非法字符并标准化空格
    text = re.sub(r'[\\/*?:"<>|]', " ", text)
    return " ".join(text.split()).strip()

def find_local_cover(query):
    """在本地目录搜索匹配的封面"""
    if not os.path.exists(LOCAL_COVER_DIR):
        return None
    
    query_clean = clean_term(query).lower()
    keywords = [k for k in re.split(r'[-\s]', query_clean) if len(k) > 1]
    
    print(f"🔎 正在本地检索: {keywords}")
    
    best_match = None
    max_hits = 0
    
    for file in os.listdir(LOCAL_COVER_DIR):
        if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
            
        file_lower = file.lower()
        # 计算匹配的关键词数量
        hits = sum(1 for kw in keywords if kw in file_lower)
        
        if hits > max_hits:
            max_hits = hits
            best_match = os.path.join(LOCAL_COVER_DIR, file)
            
    # 阈值：至少匹配一半的关键词，或者关键词较少时至少匹配一个
    if max_hits >= max(1, len(keywords) // 2):
        print(f"✅ 找到本地匹配: {best_match}")
        return best_match
        
    return None

def process_to_jpg(input_path, output_filename=None):
    """将图片处理为正方形 JPG"""
    try:
        img = Image.open(input_path)
        # 裁剪正方形
        w, h = img.size
        if w != h:
            min_dim = min(w, h)
            left = (w - min_dim) / 2
            top = (h - min_dim) / 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            
        # 准备输出路径
        if output_filename:
            output_path = os.path.join(LOCAL_COVER_DIR, output_filename)
        else:
            # 如果是本地文件且已经是 jpg 且是正方形，可能不需要重新保存，但为了规范建议统一处理
            name = Path(input_path).stem
            output_path = os.path.join(LOCAL_COVER_DIR, f"{name}.jpg")
            
        # 转换并保存
        img.convert('RGB').save(output_path, 'JPEG', quality=95)
        return output_path
    except Exception as e:
        print(f"❌ 图片处理失败: {e}")
        return None

def download_itunes_cover(query):
    """联网下载封面"""
    term = clean_term(query)
    print(f"🌐 正在联网检索: {term}")
    try:
        params = {"term": term, "media": "music", "entity": "song", "limit": 1}
        resp = requests.get(ITUNES_API_URL, params=params, timeout=15)
        data = resp.json()
        
        if data["resultCount"] > 0:
            result = data["results"][0]
            cover_url = result["artworkUrl100"].replace("100x100bb", "1000x1000bb")
            print(f"✅ 找到网络封面: {cover_url}")
            
            img_resp = requests.get(cover_url, timeout=20)
            img_data = io.BytesIO(img_resp.content)
            
            # 使用现有逻辑处理并保存
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", term)
            return process_to_jpg(img_data, f"{safe_name}.jpg")
    except Exception as e:
        print(f"❌ 联网下载失败: {e}")
    return None

def get_best_cover(query):
    """统一接口：本地优先 -> 联网备份"""
    # 1. 本地尝试
    local_path = find_local_cover(query)
    if local_path:
        # 如果是本地图，确保它是 JPG 且是正方形
        return process_to_jpg(local_path)
        
    # 2. 网络尝试
    return download_itunes_cover(query)

if __name__ == "__main__":
    import sys
    test_query = sys.argv[1] if len(sys.argv) > 1 else "周杰伦 蛇舞"
    path = get_best_cover(test_query)
    if path:
        print(f"✨ 最终封面路径: {path}")
    else:
        print("💀 未能获取到任何封面")
