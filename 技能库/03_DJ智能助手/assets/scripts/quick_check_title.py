import httpx
import sys
import urllib.parse

query = urllib.parse.quote("Douyin 时常觉得命运戏弄我")
url = f"https://www.bing.com/search?q={query}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
