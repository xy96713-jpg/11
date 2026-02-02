import json
import os
from pathlib import Path

CACHE_FILE = Path(r"d:\anti\song_analysis_cache.json")

def verify_file_exists(p):
    try:
        return bool(p) and os.path.exists(p)
    except Exception:
        return False

def normalize_path(p):
    if not p:
        return ""
    s = str(p).replace("\\", "/")
    try:
        s = str(Path(s).resolve()).replace("\\", "/")
    except Exception:
        s = s
    return s.lower()

def load_clean_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    cleaned = {}
    for k, v in data.items():
        fp = v.get("file_path")
        if verify_file_exists(fp):
            cleaned[k] = v
    return cleaned

def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    by_path = {}
    for _, v in data.items():
        fp = v.get("file_path")
        if not fp:
            continue
        key = normalize_path(fp)
        a = v.get("analysis", {}) or {}
        by_path[key] = {
            "bpm": a.get("bpm"),
            "key": a.get("detected_key_dsp") or a.get("key"),
            "analysis": a,
        }
    return by_path

def normalize_key(k):
    if k is None:
        return None
    return str(k).strip()

def _camelot_map():
    return {
        "C Major": "8B","G Major":"9B","D Major":"10B","A Major":"11B","E Major":"12B","B Major":"1B",
        "F# Major":"2B","C# Major":"3B","G# Major":"4B","D# Major":"5B","A# Major":"6B","F Major":"7B",
        "A Minor":"8A","E Minor":"9A","B Minor":"10A","F# Minor":"11A","C# Minor":"12A","G# Minor":"1A",
        "D# Minor":"2A","A# Minor":"3A","F Minor":"4A","C Minor":"5A","G Minor":"6A","D Minor":"7A",
        # Short Notation Support
        "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B", "B": "1B",
        "F#": "2B", "Gb": "2B", "C#": "3B", "Db": "3B", "G#": "4B", "Ab": "4B", 
        "D#": "5B", "Eb": "5B", "A#": "6B", "Bb": "6B", "F": "7B",
        "Am": "8A", "Em": "9A", "Bm": "10A", "F#m": "11A", "Gbm": "11A", "C#m": "12A", "Dbm": "12A", "G#m": "1A", "Abm": "1A",
        "D#m": "2A", "Ebm": "2A", "A#m": "3A", "Bbm": "3A", "Fm": "4A", "Cm": "5A", "Gm": "6A", "Dm": "7A"
    }

def _keys_compatible(c1, c2):
    if not c1 or not c2:
        return (0, "Missing Key")
    try:
        n1, l1 = int(c1[:-1]), c1[-1]
        n2, l2 = int(c2[:-1]), c2[-1]
    except Exception:
        return (0, "Invalid Key")
    if c1 == c2:
        return (100, "Perfect Match")
    if l1 == l2 and (abs(n1 - n2) == 1 or (n1, n2) in {(12,1),(1,12)}):
        return (80, "Harmonic Neighbor")
    if n1 == n2 and l1 != l2:
        return (60, "Relative Major/Minor")
    return (0, "Incompatible")

def get_advanced_harmonic_score(k1, k2):
    m = _camelot_map()
    
    # 【V5.2 HOTFIX】安全提取 key 字符串：处理 DjmdKey 对象
    def _safe_key_str(k):
        if k is None:
            return None
        if hasattr(k, 'Name'):  # DjmdKey object
            return k.Name if k.Name else None
        return str(k).strip() if k else None
    
    k1_str = _safe_key_str(k1)
    k2_str = _safe_key_str(k2)
    
    # [V5.3] Aggressive Cleaning
    def _clean_key(k):
        if not k: return None
        # Remove " Major", " Minor" suffix variations if map lookup fails
        k = k.replace(" Major", "").replace(" Minor", "")
        k = k.replace("maj", "").replace("min", "m")
        k = k.strip()
        return k

    c1 = m.get(k1_str)
    if not c1: c1 = m.get(_clean_key(k1_str))
    
    c2 = m.get(k2_str)
    if not c2: c2 = m.get(_clean_key(k2_str))
    
    # Check if k1/k2 are already Camelot (e.g. "8A")
    if not c1 and k1_str and len(k1_str) <= 3 and k1_str[-1] in ('A', 'B') and k1_str[0].isdigit(): c1 = k1_str
    if not c2 and k2_str and len(k2_str) <= 3 and k2_str[-1] in ('A', 'B') and k2_str[0].isdigit(): c2 = k2_str
    
    if not c1 or not c2:
        return (0, f"Unknown Key Format ({k1_str}|{k2_str})")
    return _keys_compatible(c1, c2)

def get_smart_pitch_shift(k1, k2):
    """Placeholder for smart pitch shift logic."""
    return (0, "No Shift Required")

def safe_get_cached_analysis(file_path, cache):
    try:
        from enhanced_harmonic_set_sorter import get_cached_analysis as _g
    except Exception:
        _g = None
    if _g is None:
        key = normalize_path(file_path)
        entry = cache.get(key) if isinstance(cache, dict) else None
        if entry and isinstance(entry, dict):
            a = entry.get("analysis") or {}
            return a
        return {}
    res = _g(file_path, cache)
    if isinstance(res, tuple):
        res = res[0] if res and res[0] else {}
    if not isinstance(res, dict):
        return {}
    return res
