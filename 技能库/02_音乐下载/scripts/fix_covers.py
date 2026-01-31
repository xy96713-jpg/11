import os
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

def get_itunes_cover(query):
    """从 iTunes 获取高清封面"""
    print(f"正在为 '{query}' 查找 iTunes 封面...")
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['resultCount'] > 0:
            result = data['results'][0]
            # 获取 1000x1000 的高清图
            cover_url = result['artworkUrl100'].replace('100x100bb.jpg', '1000x1000bb.jpg')
            return cover_url
    except Exception as e:
        print(f"iTunes 搜索失败: {e}")
    return None

def embed_cover(mp3_path, cover_url):
    """下载并嵌入封面"""
    try:
        print(f"正在下载封面: {cover_url}")
        img_data = requests.get(cover_url, timeout=10).content
        
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
            
        # 清除旧封面
        audio.tags.delall('APIC')
        
        audio.tags.add(APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='Cover (front)',
            data=img_data
        ))
        # 强制保存为 v2.3 以兼容 Windows 资源管理器
        audio.save(v2_version=3)
        print(f"✅ 封面已成功嵌入 (v2.3): {os.path.basename(mp3_path)}")
        return True
    except Exception as e:
        print(f"封面嵌入失败: {e}")
    return False

def fix_directory(directory):
    files_to_fix = {
        'SHE_MeiliXinShijie_Official.mp3': 'S.H.E 美丽新世界',
        'TTS_Stay.mp3': 'TaeTiSeo Stay Holler'
    }
    
    for filename, query in files_to_fix.items():
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            # 检查是否有封面 (简单逻辑: 检查 APIC 标签)
            try:
                audio = MP3(path)
                if not any(key.startswith('APIC') for key in audio.tags.keys()):
                    print(f"发现缺失封面的文件: {filename}")
                    cover_url = get_itunes_cover(query)
                    if cover_url:
                        embed_cover(path, cover_url)
                else:
                    print(f"文件已有封面: {filename}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {e}")

if __name__ == "__main__":
    fix_directory(r"D:\song\Final_Music_Official")
