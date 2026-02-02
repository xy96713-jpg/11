import requests
import sys

def test_api(spotify_id):
    url = f"https://api.spotifydown.com/metadata/track/{spotify_id}"
    headers = {
        "Origin": "https://spotifydown.com",
        "Referer": "https://spotifydown.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    track_id = "39Yp9IuG7Cb93T7O6v9oBs"
    test_api(track_id)
