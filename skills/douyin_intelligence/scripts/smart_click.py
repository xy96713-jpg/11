import asyncio
from playwright.async_api import async_playwright
import os
import sys
import json

async def smart_click(url, selector, output_path):
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
            print(f"[*] Navigating to: {url}", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10) # Heavy wait for Douyin
            
            # Find the card and its coordinates
            card = await page.query_selector(selector)
            if card:
                box = await card.bounding_box()
                if box:
                    center_x = box["x"] + box["width"] / 2
                    center_y = box["y"] + box["height"] / 2
                    print(f"[+] Found Target at ({center_x}, {center_y}). Performing Human-like Click...", file=sys.stderr)
                    
                    # Move mouse and click
                    await page.mouse.move(center_x, center_y)
                    await asyncio.sleep(1)
                    await page.mouse.click(center_x, center_y)
                    
                    print("[*] Waiting for modal jump...", file=sys.stderr)
                    await asyncio.sleep(8)
                    
                    final_url = page.url
                    print(f"[*] Jump Result: {final_url}", file=sys.stderr)
                    await page.screenshot(path=os.path.join(output_path, "smart_click_result.png"))
                    
                    success = "modal_id" in final_url or "video" in final_url
                    with open(os.path.join(output_path, "smart_click_summary.json"), "w") as f:
                        json.dump({"success": success, "url": final_url}, f)
                else:
                    print("[!] Element found but has no bounding box.", file=sys.stderr)
            else:
                print(f"[!] Selector '{selector}' not found on page.", file=sys.stderr)

        except Exception as e:
            print(f"[!] Click Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    t_url = sys.argv[1]
    sel = sys.argv[2]
    out = sys.argv[3]
    asyncio.run(smart_click(t_url, sel, out))
