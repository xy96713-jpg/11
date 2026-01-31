import asyncio
from playwright.async_api import async_playwright
import os

async def check_current_view():
    user_data_dir = "d:\\anti\\gemini_nano_profile"
    screenshot_path = "d:\\anti\\current_chrome_view.png"
    
    async with async_playwright() as p:
        print("[*] Attempting to connect to/launch Chrome for visual audit...")
        # Since we want to see what's happening in the profile we just launched
        try:
            # We use launch_persistent_context to see the same state the user sees
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True, # We'll do this in background to avoid flickering
                args=["--no-first-run"]
            )
            page = context.pages[0]
            
            # Check a few likely URLs
            urls_to_check = [
                "chrome://flags",
                "chrome://components",
                "https://www.google.com"
            ]
            
            for url in urls_to_check:
                print(f"[*] Navigating to {url} for diagnostic...")
                await page.goto(url)
                await asyncio.sleep(3)
                safe_name = url.replace("://", "_").replace("/", "_").replace("#", "_")
                path = f"d:\\anti\\diag_{safe_name}.png"
                await page.screenshot(path=path)
                print(f"[+] Saved diagnostic screenshot to {path}")
            
            await context.close()
        except Exception as e:
            print(f"[-] Diagnostic failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_current_view())
