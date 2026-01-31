import psutil

def check_chrome_flags():
    print("[*] Auditing Chrome processes...")
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    found = True
                    print(f"\n[PID: {proc.info['pid']}]")
                    print("Command Line: " + " ".join(cmdline))
                    if "enable-features" in " ".join(cmdline):
                        print("[!] AI Features detected in command line!")
                    else:
                        print("[?] No AI features found in this process.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if not found:
        print("[-] No Chrome processes found running.")

if __name__ == "__main__":
    check_chrome_flags()
