import asyncio
from playwright.async_api import async_playwright
import json
import os
import sys

async def devtools_perception(url, output_path):
    print(f"[*] Initializing DevTools-Level Perception for: {url}", file=sys.stderr)
    
    # Session storage path
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(user_data_dir, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        # 1. Launch Persistent Context
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 2. Setup Network Interception via CDP
        client = await page.context.new_cdp_session(page)
        await client.send("Network.enable")
        
        captured_data = []

        async def on_response(response):
            # Target Douyin's detail API
            if "aweme/v1/web/aweme/detail" in response.url:
                try:
                    body = await response.json()
                    item = body.get("aweme_detail", {})
                    video_url = item.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]
                    
                    if video_url:
                        print(f"[+] HD Video URL Intercepted!", file=sys.stderr)
                        captured_data.append({
                            "type": "detail_api",
                            "video_url": video_url,
                            "title": item.get("desc", "Unknown"),
                            "author": item.get("author", {}).get("nickname", "Unknown"),
                            "raw": body
                        })
                        # Save a snapshot immediately
                        with open(os.path.join(output_path, "intercepted_raw_api.json"), "w", encoding="utf-8") as f:
                            json.dump(body, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    pass

        page.on("response", on_response)

        try:
            print("[*] Navigating to target...", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=0)
            
            print("\n" + "="*50, file=sys.stderr)
            print("🔬 DEVTOOLS AUTO-PILOT ACTIVE 🔬", file=sys.stderr)
            print("1. Please solve the Captcha if it appears.", file=sys.stderr)
            print("2. I am WATCHING the data stream in the background.", file=sys.stderr)
            print("3. Once I catch the video data, I will AUTO-COMPLETE.", file=sys.stderr)
            print("="*50 + "\n", file=sys.stderr)
            
            # --- SMART POLLING LOOP (Replaces manual input) ---
            wait_time = 0
            max_wait = 300 # 5 minutes timeout
            
            while wait_time < max_wait:
                # Condition 1: We caught the API data
                # Condition 2: We are NOT on a verify page (URL doesn't contain 'verify')
                current_url = page.url
                if len(captured_data) > 0 and "verify" not in current_url:
                    print(f"[+] Success detected! Data captured from: {current_url}", file=sys.stderr)
                    print("[*] Waiting 5 more seconds to stabilize capture...", file=sys.stderr)
                    await asyncio.sleep(5)
                    break
                
                if "verify" in current_url:
                    if wait_time % 10 == 0:
                        print("[!] Block detected: Waiting for Human to solve Captcha...", file=sys.stderr)
                
                await asyncio.sleep(1)
                wait_time += 1
            
            if wait_time >= max_wait:
                print("[!] Timeout: Captcha not solved or data not found.", file=sys.stderr)
            
            print(f"[*] Perception Sequence Finished successfully.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Critical Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CDP-based Network Perception")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--output", default=os.getcwd(), help="Output directory")
    args = parser.parse_args()
    
    asyncio.run(devtools_perception(args.url, args.output))
