import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def extract_cookies(target_site, output_path):
    user_data_dir = "D:\\anti\\browser_profile"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # We don't navigate! We just look at what's currently in the context.
            # Cookies should be available from the persistent profile immediately.
            await asyncio.sleep(2)
            
            cookies = await context.cookies()
            if not cookies:
                print("[!] No cookies found in context. Trying a quick navigation to about:blank...", file=sys.stderr)
                await page.goto("about:blank", timeout=5000)
                cookies = await context.cookies()
            
            # Convert to Netscape format
            netscape_lines = ["# Netscape HTTP Cookie File", "# http://curl.haxx.se/rfc/cookie_spec.html", "# This is a generated file!  Do not edit.", ""]
            for c in cookies:
                # domain, flag, path, secure, expiration, name, value
                domain = c['domain']
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c['path']
                secure = "TRUE" if c['secure'] else "FALSE"
                expires = int(c.get('expires', -1))
                if expires == -1: expires = 0 # Session cookie
                name = c['name']
                value = c['value']
                
                line = f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
                netscape_lines.append(line)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(netscape_lines))
                
            print(f"[+] Cookies exported to: {output_path}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[!] Cookie Extraction Error: {e}", file=sys.stderr)
            return False
        finally:
            await context.close()

if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else "https://www.douyin.com"
    out = sys.argv[2] if len(sys.argv) > 2 else "douyin_cookies.txt"
    asyncio.run(extract_cookies(site, out))
