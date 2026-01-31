
keywords = ['rock', 'boat', 'good', 'up', 'orb', 'reads', 'bro', 'season', 'ps118']
try:
    with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-16-le') as f:
        lines = f.readlines()
except:
    with open(r'd:\anti\yuki_videos.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

print("--- Matches ---")
for line in lines:
    line_lower = line.lower()
    # Relaxing the 'xg' constraint to find potential mislabeled tracks from the same uploader
    for k in keywords:
        if k in line_lower:
            print(line.strip())
