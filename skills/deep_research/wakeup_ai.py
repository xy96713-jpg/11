import asyncio
from playwright.async_api import async_playwright

async def wakeup_ai():
    print("[*] Connecting to Chrome to WAKE UP the AI model...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            # 1. Force call the API to trigger internal registration
            print("[*] Triggering API call (might fail, that's okay)...")
            try:
                # We try to access it. If it's undefined, we try to access optimizationGuide
                js_trigger = '''async () => {
                    console.log("Attempting to access window.ai...");
                    if (window.ai) {
                        try {
                            await window.ai.canCreateTextSession();
                            return "Called canCreateTextSession";
                        } catch (e) { return "Error calling session: " + e.message; }
                    } else {
                        return "window.ai is undefined";
                    }
                }'''
                trigger_result = await page.evaluate(js_trigger)
                print(f"[+] Trigger Result: {trigger_result}")
            except Exception as e:
                print(f"[-] Trigger Exception: {e}")

            # 2. Check Components List Content (Debug)
            print("[*] Dumping component list to debug...")
            await page.goto("chrome://components")
            await asyncio.sleep(2)
            
            # Get all text content
            content = await page.evaluate("document.body.innerText")
            if "Optimization Guide" in content:
                print("[!] FOUND 'Optimization Guide' in text content!")
            else:
                print("[-] 'Optimization Guide' NOT found in page text.")
                # Save text to file for agent to see
                with open("d:\\anti\\components_dump.txt", "w", encoding="utf-8") as f:
                    f.write(content)
            
            await browser.close()
        except Exception as e:
            print(f"[-] Wakeup error: {e}")

if __name__ == "__main__":
    asyncio.run(wakeup_ai())
