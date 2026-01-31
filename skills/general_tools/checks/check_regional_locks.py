import json
import os

def check_regional_locks():
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome SxS", "User Data", "Local State")
    if not os.path.exists(local_state_path):
        print(f"[!] Path not found: {local_state_path}")
        return

    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            v_country = data.get('variations_country', 'NOT_SET')
            v_perm = data.get('variations_permanent_consistency_country', 'NOT_SET')
            print(f"[*] variations_country: {v_country}")
            print(f"[*] variations_permanent_consistency_country: {v_perm}")
    except Exception as e:
        print(f"[ERROR] Failed to read: {e}")

if __name__ == "__main__":
    check_regional_locks()
