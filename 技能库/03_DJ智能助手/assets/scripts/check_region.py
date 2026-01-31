import asyncio
import os
from playwright.async_api import async_playwright

async def check_region_access():
    os.environ["HOME"] = "C:\\Users\\Administrator"
    async with async_playwright() as p:
        # We use a clean browser instance (no profile)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        url = "https://aistudio.google.com/"
        print(f"[*] Attempting to reach: {url}")
        
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            final_url = page.url
            title = await page.title()
            
            print(f"[+] Final URL: {final_url}")
            print(f"[+] Page Title: {title}")
            
            # Save screenshot
            screenshot_path = "D:\\anti\\regional_access_check.png"
            await page.screenshot(path=screenshot_path)
            print(f"[+] Screenshot saved to {screenshot_path}")
            
            if "unsupported" in final_url:
                print("[!] Result: BLOCKED (Redirected to unsupported)")
            elif "ServiceLogin" in final_url or "accounts.google.com" in final_url:
                print("[+] Result: SUCCESS (Reached Login Portal)")
            else:
                print("[?] Result: UNCERTAIN (Check screenshot)")
                
        except Exception as e:
            print(f"[-] Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_region_access())
