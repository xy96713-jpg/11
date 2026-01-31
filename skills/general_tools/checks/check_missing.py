
keywords = ['rain', 'space', 'star', 'love', 'iykyk', 'something', 'woke']
try:
    with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-16-le') as f:
        lines = f.readlines()
except:
    with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

print("--- Matches ---")
for line in lines:
    line_lower = line.lower()
    if 'xg' in line_lower:
        for k in keywords:
            if k in line_lower:
                print(line.strip())
