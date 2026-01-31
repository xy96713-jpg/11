import yt_dlp
import sys

# 设置控制台输出编码为 UTF-8，以防止中文乱码
sys.stdout.reconfigure(encoding='utf-8')

def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
        'ignoreerrors': True,
    }

    print(f"\nSearching for: {query} ...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # ytsearch10 will return top 10 results
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            if 'entries' in info:
                found = False
                for entry in info['entries']:
                    if not entry: continue
                    title = entry.get('title', 'No Title')
                    video_id = entry.get('id')
                    duration = entry.get('duration', 0)
                    uploader = entry.get('uploader', 'Unknown')
                    
                    if video_id:
                        print(f"- [Title] {title}")
                        print(f"  [Link]  https://youtu.be/{video_id}")
                        print(f"  [Time]  {duration}s")
                        print(f"  [User]  {uploader}")
                        print("-" * 30)
                        found = True
                
                if not found:
                    print("No valid entries found.")
            else:
                print("No entries structure returned.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    search_youtube("XG Hypnotize Official Audio")
    search_youtube("XG Hypnotize")
