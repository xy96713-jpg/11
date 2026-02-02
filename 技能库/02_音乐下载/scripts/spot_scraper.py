import requests
from bs4 import BeautifulSoup
import sys
import re

def get_spotify_title(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试从 <title> 标签获取信息
        # 格式通常为 "Song Name - Artist - Song | Spotify"
        title_text = soup.title.string if soup.title else ""
        print(f"DEBUG: Raw Title -> {title_text}")
        
        if not title_text or "Spotify" not in title_text:
            # 尝试从 Open Graph 标签获取
            og_title = soup.find("meta", property="og:title")
            if og_title:
                return og_title["content"]
        
        # 清理标题
        clean_title = title_text.replace(" | Spotify", "").split(" - Spotify")[0].strip()
        # 有些可能是 "Song Name · Artist"
        clean_title = clean_title.replace(" · ", " - ")
        
        return clean_title

    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spot_scraper.py [URL]")
    else:
        print(get_spotify_title(sys.argv[1]))
