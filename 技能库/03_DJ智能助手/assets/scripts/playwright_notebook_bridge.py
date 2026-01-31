import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

USER_DATA_DIR = "D:\\anti\\notebooklm_playwright_profile"

async def authenticate():
    """Launch the actual system Chrome with remote debugging to bypass Google's security."""
    os.environ["HOME"] = "C:\\Users\\Administrator"
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    
    import subprocess
    print(f"[*] Launching REAL Chrome from: {chrome_path}")
    
    # Launch Chrome with remote debugging enabled
    # We use a temp directory to avoid profile locks but stay authentic
    temp_profile = "D:\\anti\\temp_chrome_profile"
    os.makedirs(temp_profile, exist_ok=True)
    
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_profile}",
        "--lang=en-US",
        "--accept-lang=en-US",
        "--no-first-run",
        "--no-default-browser-check",
        "https://notebooklm.google.com/notebook/"
    ]
    
    # Start the process non-blockingly
    subprocess.Popen(cmd)
    
    print("[!] REAL Chrome launched.")
    print("[!] PLEASE LOG IN IN THE CHROME WINDOW THAT JUST OPENED.")
    print("[!] Once logged in and you see your notebooks, just tell me 'Done'.")
    
    # We don't wait for process exit here because we want to keep the session alive
    # and let the user interact with it.
    print("[*] Bridge is now in 'Monitoring' mode. Waiting for your confirmation.")

async def verify_remote():
    """Connect to the already running REAL Chrome and verify access."""
    os.environ["HOME"] = "C:\\Users\\Administrator"
    async with async_playwright() as p:
        try:
            # Connect to the existing chrome instance
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print(f"[*] Connected. Current Page Title: {await page.title()}")
            
            # Navigate to the specific notebook link
            target_url = "https://notebooklm.google.com/notebook/4741957b-f358-48fb-a16a-da8d20797bc6"
            print(f"[*] Ensuring we are at the target notebook...")
            await page.goto(target_url, wait_until="networkidle")
            
            # WAITING for actual content that confirms we are INSIDE
            # NotebookLM uses a complex UI, we wait for the main content area or sources list
            print("[*] Waiting for notebook content to render (Timeout: 20s)...")
            try:
                # This selector is common for the source list in NotebookLM
                await page.wait_for_selector("source-list, .source-list-container, [role='main']", timeout=20000)
                print("[+] SUCCESS: Notebook content detected!")
            except:
                print("[!] Warning: Specific content elements not found, taking screenshot anyway.")
            
            # Capture evidence
            screenshot_path = "D:\\anti\\notebooklm_authenticated_proof.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"[+] Authenticated proof saved to {screenshot_path}")
            
            await browser.close()
        except Exception as e:
            print(f"[-] Verification failed: {e}")

async def ask_notebook(query):
    """Input a query into the NotebookLM chat and get response."""
    os.environ["HOME"] = "C:\\Users\\Administrator"
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            # Look for the chat input - NotebookLM uses a complex textarea or role=textbox
            # We use a broad selector for the chat input
            selector = "textarea[placeholder*='在此输入'], textarea[placeholder*='Ask'], div[contenteditable='true']"
            await page.wait_for_selector(selector)
            await page.fill(selector, query)
            await page.keyboard.press("Enter")
            
            print(f"[*] Query sent: {query}. Waiting for response...")
            await asyncio.sleep(10) # Wait for AI to generate
            
            # Capture the latest response
            # Usually the last message in the chat container
            # This is a bit brittle but common for simple bridges
            responses = await page.query_selector_all(".message-content, [role='log']")
            if responses:
                last_response = await responses[-1].inner_text()
                print(f"[+] Response: {last_response[:200]}...")
            
            await browser.close()
        except Exception as e:
            print(f"[-] Query failed: {e}")

async def check_aistudio():
    """Check and EXAMINE access to Google AI Studio dashboard."""
    os.environ["HOME"] = "C:\\Users\\Administrator"
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print("[*] Examining AI Studio state...")
            # Navigate if not already there
            if "aistudio.google.com" not in page.url:
                await page.goto("https://aistudio.google.com/", wait_until="networkidle")
            
            # SELF-EXAMINATION: Look for authenticated elements
            # AI Studio Dashboard markers: "New Chat" button, history sidebar, or user avatar
            dashboard_selectors = [
                "button:has-text('Create')", 
                "ms-nav-item", 
                "ms-user-avatar",
                ".chat-input-container"
            ]
            
            is_authenticated = False
            for selector in dashboard_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        is_authenticated = True
                        print(f"[!] Self-Examination SUCCESS: Detected '{selector}' - We are INSIDE.")
                        break
                except:
                    continue
            
            if not is_authenticated:
                print("[?] Self-Examination: Still on Login or Landing page.")
            
            # Capture evidence with descriptive name
            suffix = "authenticated" if is_authenticated else "login_only"
            screenshot_path = f"D:\\anti\\aistudio_{suffix}_proof.png"
            await page.screenshot(path=screenshot_path)
            print(f"[+] AI Studio snapshot ({suffix}) saved to {screenshot_path}")
            
            await browser.close()
            return is_authenticated
        except Exception as e:
            print(f"[-] AI Studio examination failed: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bridge.py [auth|verify|ask|aistudio] [args]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "auth":
        asyncio.run(authenticate())
    elif mode == "verify":
        asyncio.run(verify_remote())
    elif mode == "ask":
        query = sys.argv[2] if len(sys.argv) > 2 else "总结一下这个笔记本"
        asyncio.run(ask_notebook(query))
    elif mode == "aistudio":
        asyncio.run(check_aistudio())
