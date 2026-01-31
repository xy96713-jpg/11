import json
import os
import tempfile
from pathlib import Path

DEFAULT_CACHE_PATH = r"d:\anti\song_analysis_cache.json"

def load_cache(cache_path=DEFAULT_CACHE_PATH):
    """
    安全读取缓存文件
    """
    if not os.path.exists(cache_path):
        return {}
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  [CacheError] Failed to load cache: {e}")
        return {}

def save_cache_atomic(cache, cache_path=DEFAULT_CACHE_PATH):
    """
    原子化保存缓存：
    1. 写入临时文件
    2. 刷新到磁盘 (flush + fsync)
    3. 重命名覆盖原文件 (原子操作)
    """
    cache_dir = os.path.dirname(cache_path)
    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(dir=cache_dir, prefix="cache_temp_", suffix=".json")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno()) # 确保写入硬件
        
        # Windows 下直接 rename 到已存在文件会报错，需要先处理
        if os.path.exists(cache_path):
            backup_path = cache_path + ".bak"
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(cache_path, backup_path)
            except Exception:
                pass
        
        os.rename(temp_path, cache_path)
        return True
    except Exception as e:
        print(f"  [CacheError] Atomic save failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

if __name__ == "__main__":
    # 测试代码
    test_cache = {"test_key": {"val": 123}}
    if save_cache_atomic(test_cache, "test_cache.json"):
        print("Atomic save success.")
        os.remove("test_cache.json")
        if os.path.exists("test_cache.json.bak"):
            os.remove("test_cache.json.bak")
