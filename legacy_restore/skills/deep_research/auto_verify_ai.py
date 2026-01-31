import os
import subprocess
import asyncio
from playwright.async_api import async_playwright

def launch_chrome_debug():
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    user_data_dir = "d:\\anti\\gemini_nano_profile"
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        
    cmd = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        "--remote-debugging-port=9222",
        "--enable-features=OptimizationGuideOnDeviceModel,PromptApiForGeminiNano",
        "--optimization-guide-on-device-model=enabled-bypass-perf-requirement",
        "--disable-field-trial-config",  # FORCE local flags
        "about:blank"
    ]
    
    print(f"[*] Launching Chrome (Debug Mode 9222) with Field Trial Disabled...")
    subprocess.Popen(cmd)

async def check_window_ai():
    print("[*] Connecting to Chrome...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            if not context.pages:
                page = await context.new_page()
            else:
                page = context.pages[0]
            
            # CRITICAL: window.ai might only be available in secure contexts (HTTPS)
            print("[*] Navigating to HTTPS context (google.com)...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            print(f"[*] Connected! Page title: {await page.title()}")
            
            # Check window.ai
            result = await page.evaluate("async () => { return window.ai ? await window.ai.canCreateTextSession() : 'UNDEFINED'; }")
            print(f"[RESULT] window.ai status: {result}")
            
            if result == 'UNDEFINED':
                 print("[-] Still UNDEFINED. Trying to force component update again...")
                 await page.goto("chrome://components")
                 await asyncio.sleep(1)
                 # Try to click update if exists
                 await page.evaluate("document.querySelectorAll('button').forEach(b => b.click())")
            
            await browser.close()
            return result
        except Exception as e:
            print(f"[-] Error: {e}")
            return str(e)

if __name__ == "__main__":
    launch_chrome_debug()
    # Give it a moment to start
    import time
    time.sleep(5)
    asyncio.run(check_window_ai())
