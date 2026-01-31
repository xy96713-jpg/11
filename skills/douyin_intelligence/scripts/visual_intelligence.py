import asyncio
from playwright.async_api import async_playwright
import os
import sys
import json

async def visual_intel(target_text, output_path):
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
            # We assume we are ALREADY on the page from previous runs
            # but we'll reload once to be sure
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(10)
            
            print(f"[*] Visual Intelligence Scanning for: {target_text}", file=sys.stderr)
            
            # 1. Scan for all links and text elements
            elements = await page.evaluate(f"""() => {{
                const targets = [];
                document.querySelectorAll('a, button, [role="button"], span').forEach(el => {{
                    if (el.innerText.includes("{target_text}")) {{
                        const rect = el.getBoundingClientRect();
                        targets.append({{
                            text: el.innerText,
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            tag: el.tagName
                        }});
                    }}
                }});
                return targets;
            }}""")
            
            print(f"[*] Found {len(elements)} potential targets.", file=sys.stderr)
            
            # 2. Heuristic: Click the one that looks most like a video title or cover
            if elements:
                target = elements[0]
                print(f"[+] Targeting: {target['text']} at ({target['x']}, {target['y']})", file=sys.stderr)
                await page.mouse.move(target['x'], target['y'])
                await asyncio.sleep(1)
                await page.mouse.click(target['x'], target['y'])
                
                await asyncio.sleep(8)
                print(f"[*] Final URL: {page.url}", file=sys.stderr)
            
            # 3. Final visual proof
            await page.screenshot(path=os.path.join(output_path, "visual_intel_final.png"))
            
        except Exception as e:
            print(f"[!] Intel Error: {e}", file=sys.stderr)
        finally:
            await context.close()

if __name__ == "__main__":
    t_text = sys.argv[1] # e.g. "江昊"
    out = sys.argv[2]
    asyncio.run(visual_intel(t_text, out))
