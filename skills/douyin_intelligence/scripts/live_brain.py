import asyncio
from playwright.async_api import async_playwright
import os
import sys
import json

async def live_brain(target_modal_id, output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080}
        )
        
        try:
            # 1. SCAN ALL OPEN PAGES
            pages = context.pages
            print(f"[*] Scanning {len(pages)} open tabs...", file=sys.stderr)
            
            target_page = None
            for p_idx, page in enumerate(pages):
                url = page.url
                title = await page.title()
                print(f"  [{p_idx}] Tab: {url} ({title})", file=sys.stderr)
                if "douyin.com" in url:
                    target_page = page
            
            if not target_page:
                print("[!] No Douyin tabs found. Opening fresh...", file=sys.stderr)
                target_page = await context.new_page()
                await target_page.goto("https://www.douyin.com", wait_until="domcontentloaded")

            # 2. IDENTIFY AND ACT
            current_url = target_page.url
            print(f"[*] Focused on Tab: {current_url}", file=sys.stderr)
            
            # Check if we need to click the search result
            if "search" in current_url and target_modal_id:
                print(f"[*] Search results detected. Attempting to click video: {target_modal_id}", file=sys.stderr)
                video_card = await target_page.query_selector("a[href*='" + target_modal_id + "']")
                if video_card:
                    await video_card.click()
                    print("[+] Clicked target video.", file=sys.stderr)
                    await asyncio.sleep(5)
            
            # 3. TAKE FINAL SNAPSHOT
            screenshot_path = os.path.join(output_path, "live_brain_focus.png")
            await target_page.screenshot(path=screenshot_path)
            
            # 4. REPORT
            analysis = {
                "url": target_page.url,
                "title": await target_page.title(),
                "is_modal": "modal_id" in target_page.url,
                "screenshot": screenshot_path
            }
            with open(os.path.join(output_path, "live_brain_summary.json"), "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2)

            print("[+] Live Brain analysis complete.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Brain Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    m_id = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2]
    asyncio.run(live_brain(m_id, out))
