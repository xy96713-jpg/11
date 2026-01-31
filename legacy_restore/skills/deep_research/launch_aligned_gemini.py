import os
import subprocess

def launch_official_aligned_chrome():
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    # Use the real Canary (SxS) user data directory
    user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome SxS", "User Data")
    
    cmd = [
        chrome_path,
        # IMPORTANT: Use default profile to ensure signed-in state
        f"--user-data-dir={user_data_dir}",
        "--remote-debugging-port=9222", # Added to allow me to operate it for you
        "--lang=en-US", # Official Requirement
        "--enable-features=OptimizationGuideOnDeviceModel,PromptApiForGeminiNano", # Required Flags
        "--optimization-guide-on-device-model=enabled-bypass-perf-requirement", # Bypass for low-end/VM
        "chrome://on-device-internals", # Direct to the monitor page
        "https://www.google.com" # And a test context
    ]
    
    print(f"[*] Launching Chrome with Official Alignment...")
    print(f"[*] Command: {' '.join(cmd)}")
    
    # Ensure no other chrome is blocking the profile
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
    except:
        pass
        
    subprocess.Popen(cmd)
    print(f"[+] Chrome launched. Please ensure you are SIGNED IN to your Google account in the window.")

if __name__ == "__main__":
    launch_official_aligned_chrome()
