import asyncio
from playwright.async_api import async_playwright
import os
import sys
import time

async def take_notes(url, output_path):
    print(f"[*] Initializing Note-Taker for: {url}", file=sys.stderr)
    async with async_playwright() as p:
        # Headful for User Interaction (Captcha solving)
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("[*] Navigating to video page...", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 1. USER INTERACTION PHASE
            print("\n" + "="*50, file=sys.stderr)
            print("🚨 PLEASE INTERACT WITH THE BROWSER NOW! 🚨", file=sys.stderr)
            print("1. Close any login popups.", file=sys.stderr)
            print("2. Solve the sliding captcha if it appears.", file=sys.stderr)
            print("3. Ensure the video starts playing.", file=sys.stderr)
            print("You have 45 seconds...", file=sys.stderr)
            print("="*50 + "\n", file=sys.stderr)
            
            await page.wait_for_timeout(45000) # Give user time
            
            # 2. DATA EXTRACTION - METADATA
            print("[*] Extracting Metadata...", file=sys.stderr)
            try:
                # Try to expand description if 'expand' button exists
                try:
                    await page.click('[data-e2e="video-desc"] span', timeout=2000) 
                except: pass
                
                desc_element = await page.wait_for_selector('[data-e2e="video-desc"]', timeout=15000)
                description_text = await desc_element.inner_text()
                
                # Try to find author name
                author_element = await page.wait_for_selector('.video-info-detail .account-name', timeout=2000)
                author_name = await author_element.inner_text()
                
            except Exception as e:
                print(f"[!] Metadata extraction partial fail: {e}", file=sys.stderr)
                description_text = "Description not found."
                author_name = "Unknown Author"

            # Save Text Info
            with open(os.path.join(output_path, "note_metadata.txt"), "w", encoding="utf-8") as f:
                f.write(f"Author: {author_name}\n")
                f.write(f"Description: {description_text}\n")
            
            # 3. VISUAL EVIDENCE COLLECTION (Timestamps)
            # define timestamps to capture (in approximate ms delay)
            # Note: We can't easily 'seek' specifically without complex JS, 
            # so we will just capture current state, wait, capture again.
            
            capture_plan = [
                ("00s", "note_thumb_00s.png", 0),
                ("05s", "note_thumb_05s.png", 5000),
                ("15s", "note_thumb_15s.png", 10000), # +10s from previous
                ("End", "note_thumb_end.png", 5000)   # +5s
            ]
            
            print("[*] Starting Screenshot Sequence...", file=sys.stderr)
            
            for label, filename, wait_ms in capture_plan:
                if wait_ms > 0:
                    await page.wait_for_timeout(wait_ms)
                
                params = os.path.join(output_path, filename)
                await page.screenshot(path=params)
                print(f"    -> Captured {label} evidence: {filename}", file=sys.stderr)
                
            print("[*] Note-Taking Complete.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Note-Taking Error: {e}", file=sys.stderr)
            # Last ditch screenshot
            await page.screenshot(path=os.path.join(output_path, "error_state.png"))
            
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python douyin_note_taker.py <url>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    # Default to 'output' folder in the same directory as the script if not specified
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"[*] Output directory set to: {output_dir}")
    asyncio.run(take_notes(target_url, output_dir))
