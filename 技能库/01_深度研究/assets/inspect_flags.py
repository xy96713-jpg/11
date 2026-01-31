import asyncio
from playwright.async_api import async_playwright

async def inspect_flags():
    async with async_playwright() as p:
        # Launching with a temp profile to avoid conflicts
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("[*] Navigating to chrome://flags...")
        await page.goto("chrome://flags")
        await asyncio.sleep(5) # Wait for JS to render
        
        # Take a screenshot to verify we are there
        await page.screenshot(path="d:\\anti\\flags_inspect.png")
        print("[+] Screenshot saved to d:\\anti\\flags_inspect.png")
        
        # Try to get the list of flag names
        # chrome://flags uses shadow DOM extensively
        flags = await page.evaluate('''() => {
            const items = document.querySelectorAll('flags-app');
            if (items.length === 0) return "No flags-app found";
            return "Found flags-app";
        }''')
        print(f"[*] Inspection result: {flags}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_flags())
