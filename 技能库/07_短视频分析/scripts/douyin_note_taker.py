import asyncio
from playwright.async_api import async_playwright
import os
import sys
import time

async def take_notes(url, output_path):
    print(f"[*] Initializing Note-Taker for: {url}", file=sys.stderr)
    
    # [V8.8] Fallback: Use Dedicated 'Magic Memory' Profile
    # Reason: Main Chrome Profile is locked/unstable for automation.
    user_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_data")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
        
    print(f"[*] Loading Persistent Profile: {user_data_path}", file=sys.stderr)

    async with async_playwright() as p:
        # [V8.8] Branch between God Mode (CDP) and Bot Mode
        if "--cdp" in sys.argv:
            print("[*] Mode: Connecting to Existing Chrome (God Mode)...", file=sys.stderr)
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                page = None
                for context in browser.contexts:
                    for p_obj in context.pages:
                        if "douyin.com" in p_obj.url:
                            page = p_obj
                            print(f"    -> Attached to existing Douyin tab: {page.url[:50]}...", file=sys.stderr)
                            await page.bring_to_front()
                            break
                    if page: break
                
                if not page:
                    print("    -> Douyin tab not found. Opening new in God Mode...", file=sys.stderr)
                    context = browser.contexts[0]
                    page = await context.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                 print(f"❌ CDP Connection Failed: {e}", file=sys.stderr)
                 return
        else:
            # Plan B: Bot Profile (Slower but isolated)
            print(f"[*] Mode: Bot Profile ({user_data_path})", file=sys.stderr)
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_path,
                channel="chrome",
                headless=False, 
                args=["--start-maximized", "--no-sandbox", "--disable-gpu"],
                ignore_default_args=["--enable-automation"], 
                viewport=None, 
            )
            page = browser.pages[0] if browser.pages else await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
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
            
            # --- NEW: Direct Video Download via Playwright (Bypasses Cookie Decryption) ---
            print("[*] Attempting Direct Video Download via Browser Context...", file=sys.stderr)
            try:
                # Find video element
                video_src = await page.evaluate("() => document.querySelector('video') ? document.querySelector('video').src : null")
                if video_src:
                     print(f"    -> Found Video Source: {video_src[:50]}...", file=sys.stderr)
                     # Download using the browser's authenticated request context
                     # This carries all cookies automatically!
                     response = await page.request.get(video_src)
                     if response.status == 200:
                         video_data = await response.body()
                         video_filename = f"{author_name}_{int(time.time())}.mp4".replace(" ", "_").replace("/", "_")
                         video_path = os.path.join(output_path, video_filename)
                         with open(video_path, "wb") as f:
                             f.write(video_data)
                         print(f"    -> ✅ SUCCESS: Video saved to {video_filename}", file=sys.stderr)
                     else:
                         print(f"    -> ❌ Failed to download status: {response.status}", file=sys.stderr)
                else:
                     print("    -> ⚠️ No video tag found on page.", file=sys.stderr)
            except Exception as e:
                print(f"    -> ❌ Direct Download Error: {e}", file=sys.stderr)
            # ---------------------------------------------------------------------------

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
    # Clean sys.argv for positional extraction
    clean_args = [a for a in sys.argv if not a.startswith("-")]
    
    if len(clean_args) < 2:
        print("Usage: python douyin_note_taker.py <url> [output_dir] [--cdp]")
        sys.exit(1)
    
    target_url = clean_args[1]
    # Handle optional output dir
    if len(clean_args) >= 3:
        output_dir = clean_args[2]
    else:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"[*] Target URL: {target_url}")
    print(f"[*] Output directory set to: {output_dir}")
    asyncio.run(take_notes(target_url, output_dir))
