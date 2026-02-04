import os

try:
    with open('debug_cohesion_run_v8.log', 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - 10000))
        data = f.read()
    
    print("--- GB18030 Output ---")
    try:
        print(data.decode('gb18030', errors='ignore'))
    except Exception as e:
        print(e)
        
    print("\n--- UTF-8 Output ---")
    try:
        print(data.decode('utf-8', errors='ignore'))
    except Exception as e:
        print(e)
except Exception as e:
    print(f"Error: {e}")
