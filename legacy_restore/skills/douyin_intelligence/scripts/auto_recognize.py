import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def auto_recognize(url, output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            print(f"[*] Navigating to: {url}", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for any potential redirects
            await asyncio.sleep(5)
            
            current_url = page.url
            title = await page.title()
            print(f"[*] Recognition Point: {current_url} ({title})", file=sys.stderr)
            
            # Identify state
            state = "unknown"
            if "verify" in current_url:
                state = "captcha"
            elif "search" in current_url:
                state = "search_results"
            elif "video" in current_url or "modal_id" in current_url:
                state = "video_modal"
            elif "www.douyin.com" in current_url and len(current_url) < 30:
                state = "home_page"
                
            print(f"[+] Identified State: {state}", file=sys.stderr)
            
            # Take definitive screenshot
            await page.screenshot(path=os.path.join(output_path, "state_recognition.png"))
            
            # Dump analysis
            analysis = {
                "url": current_url,
                "title": title,
                "state": state,
                "is_logged_in": await page.evaluate("() => document.body.innerText.includes('消息') || document.body.innerText.includes('个人中心')")
            }
            
            with open(os.path.join(output_path, "recognition_summary.json"), "w", encoding="utf-8") as f:
                import json
                json.dump(analysis, f, indent=2)
                
        except Exception as e:
            print(f"[!] Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    target_url = sys.argv[1]
    output = sys.argv[2]
    asyncio.run(auto_recognize(target_url, output))
