import asyncio
from playwright.async_api import async_playwright
import os
import sys
import json

async def auto_pilot(url, modal_id, output_path):
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
            print(f"[*] Auto-Pilot Navigating to Search: {url}", file=sys.stderr)
            await page.goto(url, wait_until="networkidle")
            
            # 1. Check if the modal is already open
            if "modal_id" in page.url:
                print("[*] Modal detected in URL. Checking visual presence...", file=sys.stderr)
            
            # 2. If not in modal, try to find the video on the page
            # Douyin videos in search usually have a href containing the aweme_id or a generic click area
            # We look for the modal_id in the HTML
            print(f"[*] Searching for Target Modal ID: {modal_id}", file=sys.stderr)
            
            # Simple heuristic: Click the first video card that looks like a match or just the first one
            video_card = await page.query_selector("a[href*='" + modal_id + "']")
            if not video_card:
                # Fallback to first video in the list
                video_card = await page.query_selector(".search-result-card, [data-e2e='search_result_card']")
                print("[!] Specific Modal ID card not found by href. Trying fallback first card...", file=sys.stderr)

            if video_card:
                print("[+] Clicking Video Card...", file=sys.stderr)
                await video_card.click()
                await asyncio.sleep(5) # Wait for modal to pop
            else:
                print("[!] No video cards found to click.", file=sys.stderr)

            # 3. Final Verification
            final_title = await page.title()
            print(f"[*] Final State: {page.url} ({final_title})", file=sys.stderr)
            await page.screenshot(path=os.path.join(output_path, "auto_pilot_final.png"))

        except Exception as e:
            print(f"[!] Pilot Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    target_url = sys.argv[1]
    m_id = sys.argv[2]
    out = sys.argv[3]
    asyncio.run(auto_pilot(target_url, m_id, out))
