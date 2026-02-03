import asyncio
from playwright.async_api import async_playwright
import os
import sys
import time

async def take_notes_god_mode(url, output_path):
    print(f"[*] GOD MODE: Attempting to connect to your real browser...", file=sys.stderr)
    
    async with async_playwright() as p:
        try:
            # 1. Connect to whatever browser is on 9222
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("    -> ✅ Connection Established!", file=sys.stderr)
            
            # 2. Find the Douyin tab or open a new one in the REAL session
            page = None
            for context in browser.contexts:
                for p_obj in context.pages:
                    if "douyin.com" in p_obj.url:
                        page = p_obj
                        print(f"    -> Found existing session at: {page.url[:50]}...", file=sys.stderr)
                        await page.bring_to_front()
                        break
                if page: break
            
            if not page:
                print("    -> Douyin not open. Launching in your active session...", file=sys.stderr)
                context = browser.contexts[0]
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded")

            # 3. Perform Analysis (No download to focus on control)
            print("[*] Waiting for your confirmation/interaction (45s)...", file=sys.stderr)
            await page.wait_for_timeout(45000)
            
            # Data Extraction
            print("[*] Extracting evidence...", file=sys.stderr)
            try:
                title = await page.title()
                params = os.path.join(output_path, "god_mode_evidence.png")
                await page.screenshot(path=params)
                print(f"    -> Evidence saved: {params}", file=sys.stderr)
                print(f"    -> Current Page Title: {title}", file=sys.stderr)
            except Exception as e:
                print(f"    -> Partial extraction fail: {e}", file=sys.stderr)

        except Exception as e:
            print(f"❌ CONNECTION FAILED: {e}", file=sys.stderr)
            print("\n🚨 PLEASE ENSURE YOU LAUNCHED CHROME WITH '--remote-debugging-port=9222'", file=sys.stderr)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/2Mtu4bcHfQg/"
    out = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    asyncio.run(take_notes_god_mode(url, out))
