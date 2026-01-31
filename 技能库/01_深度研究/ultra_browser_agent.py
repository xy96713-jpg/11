import asyncio
from playwright.async_api import async_playwright

async def main():
    # Note: browser-use typically needs an LLM to drive the agent's logic
    # Since I am the agent, I will use a simple playwright script as the "brain" 
    # to avoid needing the user's API key if not configured.
    # However, to use the full power of browser-use as requested, we need it to "see" the page.
    
    # Let's use a simpler but more robust implementation that handles Shadow DOM properly
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        print("[*] Starting Ultra Browser Agent...")
        # Use existing profile to keep state if needed
        context = await p.chromium.launch_persistent_context(
            user_data_dir="d:\\anti\\temp_chrome_profile",
            headless=False,
            args=[
                "--no-first-run",
                "--enable-features=OptimizationGuideOnDeviceModel,PromptApiForGeminiNano"
            ]
        )
        page = context.pages[0]
        
        async def force_set_flag(name, value_index=1):
            print(f"[*] Targeting: {name}")
            await page.goto(f"chrome://flags/#search={name}")
            await asyncio.sleep(4)
            
            # This JS strictly follows the Shadow DOM tree of Chrome 144
            success = await page.evaluate(f'''() => {{
                const app = document.querySelector('flags-app');
                if (!app) return "No app";
                const list = app.shadowRoot.querySelector('flags-experiment-list');
                if (!list) return "No list";
                const flags = list.shadowRoot.querySelectorAll('flags-experiment');
                for (let f of flags) {{
                    const title = f.shadowRoot.querySelector('.experiment-name');
                    if (title && title.innerText.toLowerCase().includes("{name.lower()}")) {{
                        const select = f.shadowRoot.querySelector('select');
                        if (select) {{
                            select.selectedIndex = {value_index};
                            select.dispatchEvent(new Event('change'));
                            return "Changed";
                        }}
                    }}
                }}
                return "Not found";
            }}''')
            print(f"[+] {name} result: {success}")

        # 1. Optimization Guide (Usually Index 1 is Enabled or Bypass)
        await force_set_flag("Optimization Guide on Device Model", 2) # 2 is usually Bypass
        
        # 2. Prompt API (Index 1 is usually Enabled)
        await force_set_flag("Prompt API for Gemini Nano", 1)
        
        # 3. Relaunch
        print("[*] Relaunching...")
        await page.evaluate('''() => {
            const app = document.querySelector('flags-app');
            app.shadowRoot.querySelector('#relaunch-button').click();
        }''')
        
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
