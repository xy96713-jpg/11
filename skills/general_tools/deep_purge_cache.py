import json
import os
from pathlib import Path

CACHE_FILE = Path(r"d:\anti\song_analysis_cache.json")

def purge_ghosts_and_duplicates():
    if not CACHE_FILE.exists():
        print("Cache file not found.")
        return

    print("🛡️ [Deep Purge] 启动深度清理...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    initial_count = len(cache)
    purged_cache = {}
    
    # 路径指纹去重（防止同一文件在缓存中存在多个不同Key的情况）
    seen_paths = set()

    for k, v in cache.items():
        fp = v.get('file_path')
        if not fp: continue
        
        # 1. 物理检查：文件是否还存在
        if not os.path.exists(fp):
            continue
            
        # 2. 规范化路径 (Windows 不区分大小写)
        norm_path = os.path.abspath(fp).lower().replace('\\', '/')
        
        # 3. 如果文件已存在且未被记录，保留它
        if norm_path not in seen_paths:
            purged_cache[k] = v
            seen_paths.add(norm_path)
        else:
            print(f"🗑️  删除重复条目: {fp}")

    final_count = len(purged_cache)
    
    # 原子保存
    temp_file = CACHE_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(purged_cache, f, ensure_ascii=False, indent=2)
    
    if CACHE_FILE.exists(): CACHE_FILE.unlink()
    temp_file.rename(CACHE_FILE)

    print(f"✅ 清理完成！")
    print(f"📊 原始条目: {initial_count}")
    print(f"📊 物理存留: {final_count}")
    print(f"📊 已移除: {initial_count - final_count}")

if __name__ == "__main__":
    purge_ghosts_and_duplicates()
