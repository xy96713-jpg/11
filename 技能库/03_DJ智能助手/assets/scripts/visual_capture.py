import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def capture_video_context(url, output_path):
    print(f"[*] Starting visual capture for: {url}", file=sys.stderr)
    async with async_playwright() as p:
        # Launch in HEADFUL mode so User can interact
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, # High Res for better OCR
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("[*] Navigating... Please complete Login/Captcha if needed!", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Give User 45 seconds to interact (Login, Verify, etc.)
            print("[*] Waiting 45s for user interaction...", file=sys.stderr)
            await page.wait_for_timeout(45000)
            
            # Additional wait to ensure video wrapper loaded
            try:
                await page.wait_for_selector('div[data-e2e="video-desc"]', state="visible", timeout=5000)
            except:
                print("[!] Video description not found, capturing state anyway.", file=sys.stderr)
                
            screenshot_path = os.path.join(output_path, "web_perception.png")
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"[*] Visual context captured at: {screenshot_path}", file=sys.stderr)
            
            # 提取页面关键文本
            content = await page.content()
            with open(os.path.join(output_path, "page_source.txt"), "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"[!] Capture failed: {e}", file=sys.stderr)
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visual_capture.py <url>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    output_dir = "D:\\temp_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    asyncio.run(capture_video_context(target_url, output_dir))
