import requests
url = "https://itunes.apple.com/search"
params = {"term": "XG HYPNOTIZE", "media": "music", "entity": "song", "limit": 1}
resp = requests.get(url, params=params)
data = resp.json()
if data["resultCount"] > 0:
    print(data["results"][0]["artworkUrl100"].replace("100x100bb", "1000x1000bb"))
