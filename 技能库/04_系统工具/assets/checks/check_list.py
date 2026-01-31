
try:
    with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-16-le') as f:
        for line in f:
            if 'XG' in line:
                print(line.strip())
except:
    try:
        with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if 'XG' in line:
                    print(line.strip())
    except Exception as e:
        print(f"Error reading file: {e}")
