import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def live_eye(output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(output_path, exist_ok=True)

    async with async_playwright() as p:
        # Connect to existing context or launch new one
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080}
        )
        
        # In persistent mode, the page might already be there
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # We don't navigate! We just look at what's currently there.
            # Wait a bit for things to settle
            await asyncio.sleep(3)
            
            url = page.url
            title = await page.title()
            print(f"[*] Live Eye connected to: {url} ({title})", file=sys.stderr)
            
            # 1. Take a screenshot
            screenshot_path = os.path.join(output_path, "live_vision.png")
            await page.screenshot(path=screenshot_path)
            
            # 2. Dump text / DOM snippets
            text_content = await page.evaluate("document.body.innerText")
            with open(os.path.join(output_path, "live_text.txt"), "w", encoding="utf-8") as f:
                f.write(text_content[:5000]) # First 5k chars
                
            print(f"[+] Snapshot captured: {screenshot_path}", file=sys.stderr)
            
        except Exception as e:
            print(f"[!] Eye Failure: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    asyncio.run(live_eye(output))
