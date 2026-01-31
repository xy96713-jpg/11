import asyncio
from playwright.async_api import async_playwright

async def final_handshake():
    print("[*] Connecting to your Chrome session...")
    async with async_playwright() as p:
        try:
            # Connect to existing browser
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Navigate to google for HTTPS context
            print("[*] Switching to google.com context...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Execute the test
            print("[*] Detecting available AI APIs...")
            js_test = """async () => {
                let status = {};
                status.window_ai = !!window.ai;
                status.window_model = !!window.model;
                status.LanguageModel = typeof LanguageModel !== 'undefined';
                
                if (window.ai && window.ai.canCreateTextSession) {
                    status.handshake = await window.ai.canCreateTextSession();
                } else if (typeof LanguageModel !== 'undefined' && LanguageModel.availability) {
                    status.handshake = await LanguageModel.availability();
                } else {
                    status.handshake = 'NONE_FOUND';
                }
                return status;
            }"""
            
            result = await page.evaluate(js_test)
            print(f"\n[🔥 RESULT] Detection: {result}")
            
            if result['handshake'] in ['readily', 'available']:
                print("[SUCCESS] Gemini Nano is LIVE!")
                # Attempt a prompt
                try:
                    out = await page.evaluate("async () => { const s = await (window.ai ? window.ai.createTextSession() : LanguageModel.create()); return await s.prompt('Hi'); }")
                    print(f"[TEST OUTPUT] {out}")
                except Exception as e:
                    print(f"[PROMPT ERROR] {e}")
            
            await browser.close()
        except Exception as e:
            print(f"[ERROR] Failed to connect or execute: {e}")

if __name__ == "__main__":
    asyncio.run(final_handshake())
