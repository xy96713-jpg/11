import os
import subprocess

def launch_gemini_chrome():
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    user_data_dir = "d:\\anti\\gemini_nano_profile"
    
    # Ensure dir exists
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        
    cmd = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        "--enable-features=OptimizationGuideOnDeviceModel,PromptApiForGeminiNano",
        "--optimization-guide-on-device-model=enabled-bypass-perf-requirement",
        "chrome://flags/#optimization-guide-on-device-model"
    ]
    
    print(f"[*] Launching Chrome with AI flags...")
    subprocess.Popen(cmd)
    print(f"[+] Chrome launched with profile: {user_data_dir}")

if __name__ == "__main__":
    launch_gemini_chrome()
