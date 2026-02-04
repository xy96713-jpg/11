
import json

cache_path = r"d:\anti\技能库\03_DJ智能助手\assets\song_analysis_cache.json"
try:
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    print(f"Total cache entries: {len(cache)}")

    # 找一个没有真实 Energy 的条目（即 Energy=50 或 None）
    empty_entry = None
    for k, v in cache.items():
        a = v.get('analysis', {})
        e = a.get('energy')
        if e is None or e == 50:
            empty_entry = v
            break
    
    if empty_entry:
        print("\n=== Sample 'Lightly Analyzed' Entry (What was actually done yesterday) ===")
        print(f"File Path: {empty_entry.get('file_path')}")
        print("Analysis Data Keys present:")
        analysis = empty_entry.get('analysis', {})
        for key in analysis.keys():
            val = analysis[key]
            # 打印值的类型或简略内容，不打印全部
            print(f"  - {key}: {type(val).__name__} (Value: {str(val)[:50]}...)")
            
    else:
        print("Could not find any entry without real energy.")

except Exception as e:
    print(f"Error: {e}")
