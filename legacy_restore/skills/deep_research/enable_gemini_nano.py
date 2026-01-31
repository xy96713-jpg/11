import asyncio
from playwright.async_api import async_playwright

async def enable_gemini_flags():
    async with async_playwright() as p:
        # We MUST use a non-default channel or properly configured instance for these flags to show up
        # We will use the main user profile if possible, or at least a stable data dir
        user_data_dir = "d:\\anti\\notebooklm_playwright_profile"
        
        print(f"[*] Launching Chrome with profile: {user_data_dir}")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # We want it visible so the user sees the progress 
            args=["--no-first-run"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        async def set_flag(search_term, value_text):
            print(f"[*] Setting flag for: {search_term} -> {value_text}")
            await page.goto(f"chrome://flags/#search={search_term}")
            await asyncio.sleep(3)
            
            # The flags page is a mess of shadow DOM
            # We use a JS helper to find and change the select element
            result = await page.evaluate(f'''() => {{
                try {{
                    const flagsApp = document.querySelector('flags-app');
                    if (!flagsApp) return "App not found";
                    
                    const experiments = flagsApp.shadowRoot.querySelector('flags-experiment-list');
                    if (!experiments) return "List not found";
                    
                    const items = experiments.shadowRoot.querySelectorAll('flags-experiment');
                    for (const item of items) {{
                        const title = item.shadowRoot.querySelector('.experiment-name');
                        if (title && title.innerText.includes("{search_term}")) {{
                            const select = item.shadowRoot.querySelector('select');
                            if (select) {{
                                // Value mapping: Default is usually 0, Enabled is 1, etc.
                                // It's better to find by text
                                const option = Array.from(select.options).find(o => o.text.includes("{value_text}"));
                                if (option) {{
                                    select.value = option.value;
                                    select.dispatchEvent(new Event('change'));
                                    return "Success set " + search_term;
                                }}
                                return "Option not found for " + search_term;
                            }}
                        }}
                    }}
                    return "Flag item not found for " + search_term;
                }} catch (e) {{
                    return "Error: " + e.message;
                }}
            }}''')
            print(f"[+] Result: {result}")
            return result

        # Enable Optimization Guide
        await set_flag("Optimization Guide on Device Model", "Bypass")
        
        # Enable Prompt API
        await set_flag("Prompt API for Gemini Nano", "Enabled")
        
        # Note: Usually a relaunch is needed. 
        # The relaunch button is at the bottom of flags-app shadow root.
        print("[*] Triggering Relaunch...")
        await page.evaluate('''() => {
            const flagsApp = document.querySelector('flags-app');
            const relaunchBtn = flagsApp.shadowRoot.querySelector('#relaunch-button');
            if (relaunchBtn) { relaunchBtn.click(); return "Relaunched"; }
            return "Relaunch button not found";
        }''')
        
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(enable_gemini_flags())
