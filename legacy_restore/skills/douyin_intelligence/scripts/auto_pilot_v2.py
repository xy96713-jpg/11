import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def auto_pilot_v2(url, modal_id, output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            print(f"[*] Navigating to: {url}", file=sys.stderr)
            # Use longer timeout for Douyin
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            print("[*] Page loaded. Scanning for video elements...", file=sys.stderr)
            await asyncio.sleep(8) # Wait for cards to render
            
            # 1. Take a 'Before' snapshot
            await page.screenshot(path=os.path.join(output_path, "pilot_v2_before.png"))
            
            # 2. Try to find the video element
            # We look for the modal_id in any href or data attribute
            video_selectors = [
                f"a[href*='{modal_id}']",
                f"[data-e2e='search_result_card']",
                ".search-result-card",
                "video" # Last resort
            ]
            
            target_el = None
            for sel in video_selectors:
                target_el = await page.query_selector(sel)
                if target_el:
                    print(f"[+] Found video element with selector: {sel}", file=sys.stderr)
                    break
            
            if target_el:
                print("[*] Clicking target video...", file=sys.stderr)
                await target_el.click()
                await asyncio.sleep(5)
                
                # Check if URL changed/modal popped
                print(f"[*] Post-Click URL: {page.url}", file=sys.stderr)
                await page.screenshot(path=os.path.join(output_path, "pilot_v2_after.png"))
                
                # Report success if in modal
                success = "modal_id" in page.url or "video" in page.url
                print(f"[+] Success Status: {success}", file=sys.stderr)
                
                with open(os.path.join(output_path, "pilot_v2_summary.json"), "w") as f:
                    import json
                    json.dump({"success": success, "url": page.url}, f)
            else:
                print("[!] Could not find target video element.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Pilot Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    t_url = sys.argv[1]
    m_id = sys.argv[2]
    out = sys.argv[3]
    asyncio.run(auto_pilot_v2(t_url, m_id, out))
