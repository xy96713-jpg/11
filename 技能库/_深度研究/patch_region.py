import json
import os
import subprocess

def patch_chrome_region():
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome SxS", "User Data", "Local State")
    
    # 1. Kill Chrome
    print("[*] Killing Chrome to release file lock...")
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
    
    if not os.path.exists(local_state_path):
        print(f"[!] Local State not found: {local_state_path}")
        return

    # 2. Patch Local State
    print("[*] Patching Local State for Region Spoofing (cn -> us)...")
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Modify country codes
        data['variations_country'] = 'us'
        if 'variations_permanent_consistency_country' in data:
            # It's often a list: [version, country]
            if isinstance(data['variations_permanent_consistency_country'], list):
               data['variations_permanent_consistency_country'][-1] = 'us'
            else:
               data['variations_permanent_consistency_country'] = 'us'
        
        # Glic eligibility (bonus)
        if 'is_glic_eligible' in data:
            data['is_glic_eligible'] = True
            
        with open(local_state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print("[SUCCESS] Local State patched.")
    except Exception as e:
        print(f"[ERROR] Patch failed: {e}")

if __name__ == "__main__":
    patch_chrome_region()
