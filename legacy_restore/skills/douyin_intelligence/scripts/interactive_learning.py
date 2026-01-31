import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def interactive_learning(url, output_path):
    print(f"[*] Initializing Persistent Interactive Learning Mode for: {url}", file=sys.stderr)
    
    # Session storage path
    user_data_dir = "D:\\anti\\browser_profile"
    os.makedirs(user_data_dir, exist_ok=True)

    async with async_playwright() as p:
        # 1. Launch Persistent Context
        # This replaces browser.launch + new_context to remember your login!
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # In persistent context, the first page is often already open
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            print("[*] Navigating...", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=0)
            
            # 2. THE MANUAL BLOCK
            print("\n" + "="*50, file=sys.stderr)
            print("🛑 HUMAN SIGNAL REQUIRED 🛑", file=sys.stderr)
            print("1. Please solve the Captcha / Login manually IN THE OPENED WINDOW.", file=sys.stderr)
            print("   (Your login will be REMEMBERED for next time!)", file=sys.stderr)
            print("2. Ensure the video is PLAYING.", file=sys.stderr)
            print("3. THEN, press 'Enter' inside this terminal or tell me 'Start' to trigger my learning.", file=sys.stderr)
            print("="*50 + "\n", file=sys.stderr)
            
            # This will wait for stdin in the background process
            input("Press Enter to continue capture...") 
            
            print("[*] Signal received! Starting 'Active Learning' sequence...", file=sys.stderr)
            
            # 3. ACTIVE CAPTURE SEQUENCE (30 Seconds Observation)
            for i in range(6): # Capture every 5 seconds for 30s
                timestamp = i * 5
                filename = f"learn_frame_{timestamp:02d}s.png"
                path = os.path.join(output_path, filename)
                
                await page.screenshot(path=path)
                print(f"    -> Captured frame at {timestamp}s: {filename}", file=sys.stderr)
                
                try:
                    text = await page.inner_text("body")
                    with open(os.path.join(output_path, f"text_log_{timestamp:02d}s.txt"), "w", encoding="utf-8") as f:
                        f.write(text)
                except: pass
                
                await page.wait_for_timeout(5000)
                
            print("[*] Learning Sequence Complete.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Critical Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Persistent Interactive Video Learning (Playwright)")
    parser.add_argument("--url", required=True, help="Target Video URL")
    parser.add_argument("--output", default=os.getcwd(), help="Output directory for frames/logs")
    args = parser.parse_args()
    
    asyncio.run(interactive_learning(args.url, args.output))
