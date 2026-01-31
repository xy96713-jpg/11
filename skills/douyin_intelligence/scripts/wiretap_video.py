import asyncio
from playwright.async_api import async_playwright
import os
import sys
import json

async def wiretap_video(url, output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"[*] Wiretapping target: {url}", file=sys.stderr)
        
        captured_data = []

        async def on_response(response):
            # Target both detail and search APIs (search results often contain full video meta)
            target_keywords = ["aweme/v1/web/aweme/detail", "aweme/v1/web/general/search", "search/item"]
            
            if any(key in response.url for key in target_keywords):
                try:
                    body = await response.json()
                    # Determine source
                    is_detail = "aweme_detail" in body
                    item = body.get("aweme_detail", {}) if is_detail else None
                    
                    # If it's a search result, find the first relevant video
                    if not item and "data" in body:
                        # Logic to find the video in search results
                        for d in body.get("data", []):
                            if d.get("type") == 1: # Video type
                                item = d.get("aweme_info", {})
                                break
                    elif not item and "aweme_list" in body:
                         item = body.get("aweme_list", [{}])[0]

                    if item:
                        video_url = item.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]
                        if video_url:
                            print(f"[+] Video Data Intercepted (Source: {response.url.split('?')[0]})!", file=sys.stderr)
                            captured_data.append({
                                "video_url": video_url,
                                "raw": body,
                                "item": item
                            })
                            # Standardize output for downloader
                            final_body = {"aweme_detail": item} if not is_detail else body
                            with open(os.path.join(output_path, "intercepted_truth.json"), "w", encoding="utf-8") as f:
                                json.dump(final_body, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            # Set a long timeout but we will likely break early
            await page.goto(url, wait_until="commit", timeout=90000)
            
            # Wait loop: Check every second if we've captured the data
            for _ in range(30): # Wait up to 30 seconds after commit
                if captured_data:
                    print("[+] Data captured early. Success.", file=sys.stderr)
                    return
                await asyncio.sleep(1)
            
            if not captured_data:
                print("[!] Data not captured yet. Scrolling...", file=sys.stderr)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(10)

        except Exception as e:
            if captured_data:
                print(f"[!] Page load exception but data was captured: {e}", file=sys.stderr)
            else:
                print(f"[!] Wiretap Failure: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    t_url = sys.argv[1]
    out = sys.argv[2]
    asyncio.run(wiretap_video(t_url, out))
