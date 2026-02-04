import codecs

print("Scanning...")
try:
    with open('debug_cohesion_run_v7.log', 'rb') as f:
        content = f.read()

    # Try split by null bytes if it's UTF-16?
    # Or just brute force decode slices?
    # Let's decode entire blob with ignore
    
    text = content.decode('utf-16', errors='ignore')
    for line in text.splitlines():
        if 'line ' in line or 'File "' in line or 'Error' in line:
            print(f"UTF16: {line.strip()}")

    text = content.decode('utf-8', errors='ignore')
    for line in text.splitlines():
        if 'line ' in line or 'File "' in line or 'Error' in line:
            print(f"UTF8: {line.strip()}")

except Exception as e:
    print(e)
