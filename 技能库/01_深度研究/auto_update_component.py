import asyncio
from playwright.async_api import async_playwright

async def auto_update_model():
    print("[*] Connecting to Chrome to force update model...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print("[*] Navigating to chrome://components...")
            await page.goto("chrome://components")
            
            # Use JS to find and click deeply in the Shadow DOM or structure
            result = await page.evaluate('''async () => {
                const components = document.querySelectorAll('div.component');
                for (const c of components) {
                    const name = c.querySelector('.component-name').innerText;
                    if (name.includes('Optimization Guide On Device Model')) {
                        const btn = c.querySelector('button.button-check-update');
                        const version = c.querySelector('.component-version').innerText;
                        
                        if (btn) {
                            btn.click();
                            return "Clicked update. Current version: " + version;
                        }
                        return "Button not found for " + name;
                    }
                }
                return "Optimization Guide component not found in list";
            }''')
            
            print(f"[+] Update Action Result: {result}")
            
            # Wait loop to check for window.ai availability
            print("[*] Waiting for window.ai to become available (Polling 60s)...")
            for i in range(12):
                await asyncio.sleep(5)
                # We need to check in a context that supports it, chrome:// might filter it
                # Let's open a new tab to google.com to test the API visibility
                status = await page.evaluate("val = (window.ai ? 'Active' : 'Missing'); val")
                print(f"   [{i*5}s] window.ai status: {status}")
                if status == 'Active':
                    print("[!!!] SUCCESS: window.ai is ready!")
                    break
            
            await browser.close()
            return result
        except Exception as e:
            print(f"[-] Automation error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(auto_update_model())
