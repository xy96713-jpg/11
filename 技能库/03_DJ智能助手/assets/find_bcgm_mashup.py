import json
import os

CACHE_FILE = r"d:\anti\song_analysis_cache.json"

def find_mashup_matches(target_title):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    target_entry = None
    for v in data.values():
        if target_title in v.get('file_path', ''):
            target_entry = v
            break
            
    if not target_entry:
        return "Target not found"
        
    base_bpm = target_entry['analysis']['bpm']
    base_key = target_entry['analysis']['key']
    matches = []
    
    # 兼容调性定义
    compatible_keys = [base_key]
    key_val = int(base_key[:-1])
    key_type = base_key[-1]
    
    # 同类型相邻
    compatible_keys.append(f"{(key_val - 2) % 12 + 1}{key_type}")
    compatible_keys.append(f"{(key_val) % 12 + 1}{key_type}")
    # 异类型同号
    compatible_keys.append(f"{key_val}{'B' if key_type == 'A' else 'A'}")
    
    # 扩大范围：123A/B 循环
    adj_up = (key_val) % 12 + 1
    adj_down = (key_val - 2) % 12 + 1
    compatible_keys = [f"{key_val}{key_type}", f"{adj_up}{key_type}", f"{adj_down}{key_type}", f"{key_val}{'B' if key_type == 'A' else 'A'}"]

    for k, v in data.items():
        if target_title in v.get('file_path', ''): continue
        
        a = v['analysis']
        bpm = a.get('bpm', 0)
        key = a.get('key', '')
        
        # BPM 容差 3%
        if abs(bpm - base_bpm) / base_bpm <= 0.03 and key in compatible_keys:
            matches.append({
                'title': os.path.basename(v['file_path']),
                'bpm': round(bpm, 2),
                'key': key,
                'energy': a.get('energy_tier', 'N/A'),
                'genres': a.get('tags', [])
            })
            
    matches.sort(key=lambda x: abs(x['bpm'] - base_bpm))
    return matches[:15]

if __name__ == "__main__":
    results = find_mashup_matches("周杰伦本草纲目")
    print(json.dumps(results, indent=2, ensure_ascii=False))
