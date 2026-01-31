import sys
import traceback
from pathlib import Path

# Add project paths
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core")

print("=== Rules Integration Verification ===")

# 1. Check Config Loader
try:
    from core.config_loader import load_dj_rules
    rules = load_dj_rules()
    print(f"[OK] Config Loader works. Rules count: {len(rules)}")
    print(f"     phrase_bars: {rules.get('phrase_bars')} (Expected: User Config or 16)")
except Exception:
    traceback.print_exc()
    print("[FAIL] Config Loader failed")

# 2. Check Auto Generator (Syntax + Signature)
try:
    import auto_hotcue_generator
    import inspect
    sig = inspect.signature(auto_hotcue_generator._generate_from_rekordbox_phrases)
    if 'dj_rules' in sig.parameters:
        print("[OK] _generate_from_rekordbox_phrases accepts dj_rules")
    else:
        print("[FAIL] _generate_from_rekordbox_phrases signature missing dj_rules")
        
except SyntaxError:
    traceback.print_exc()
    print("[FAIL] auto_hotcue_generator.py has SYNTAX ERROR")
except Exception:
    traceback.print_exc()
    print("[FAIL] Auto generator import failed")

# 3. Check Pro Cueing (Import check)
try:
    import skills.skill_pro_cueing as pro
    print("[OK] Skill Pro Cueing imported")
except Exception:
    traceback.print_exc()

print("=== End Verification ===")
