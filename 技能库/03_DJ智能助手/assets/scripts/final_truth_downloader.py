import json
import httpx
import os
import sys

async def final_download(json_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    item = data.get("aweme_detail", {})
    if not item:
        print("[!] No item detail in JSON.", file=sys.stderr)
        return
    
    # Extract Title and Video URL
    raw_title = item.get("desc", "douyin_video")[:50]
    # Clean title for filename: remove ALL non-alphanumeric/Chinese/safe chars
    import re
    # Replace newlines and illegal chars with underscore
    title = re.sub(r'[\s\\/*?:"<>|#· @]+', "_", raw_title).strip("_")
    if not title:
        title = "video_" + str(item.get("aweme_id", "0"))
    
    # Try the highest quality bit_rate if available
    bit_rates = item.get("video", {}).get("bit_rate", [])
    if bit_rates:
        # Sort by bit_rate or just pick the first (usually highest in web detail)
        # But let's look for one with 'uri'
        url = bit_rates[0].get("play_addr", {}).get("url_list", [None])[0]
    else:
        url = item.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]

    if not url:
        print("[!] No video URL found in JSON.", file=sys.stderr)
        return

    output_path = os.path.join(output_dir, f"{title}.mp4")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Referer": "https://www.douyin.com/"
    }

    print(f"[*] Downloading from Truth URL: {url[:100]}...", file=sys.stderr)
    
    # Download with httpx
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=120) as client:
        try:
            async with client.stream("GET", url) as response:
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                    print(f"[+] Download Finished: {output_path}", file=sys.stderr)
                    return {"status": "success", "path": output_path, "title": item.get("desc")}
                else:
                    print(f"[!] Download Failed: HTTP {response.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[!] Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    j_path = sys.argv[1]
    out = sys.argv[2]
    import asyncio
    res = asyncio.run(final_download(j_path, out))
    if res:
        print(json.dumps(res, ensure_ascii=False))
