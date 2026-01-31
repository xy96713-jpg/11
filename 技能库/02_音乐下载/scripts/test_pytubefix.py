
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

def download_test():
    # Hearts2Hearts FOCUS video ID (from previous logs) if available, or just search
    # Since we don't have the ID handy from logs (it was 403), let's try a known persistent 403 video if we can find one, 
    # or just use the search term logic which pytubefix can also do via Search.
    
    # Let's try to search first
    from pytubefix import Search
    
    query = "Hearts2Hearts FOCUS audio"
    print(f"Searching for: {query}")
    s = Search(query)
    
    if len(s.videos) == 0:
        print("No videos found.")
        return

    video = s.videos[0]
    print(f"Found video: {video.title} ({video.video_id})")
    
    # Try to get the stream URL (this is usually where 403 happens)
    try:
        print("Attempting to bypass bot check via PO Token...")
        # 'WEB' client is often default, but can be explicit. 
        # pytubefix handles PO Token internally if we use the right client.
        
        # We want audio only
        ys = video.streams.get_audio_only()
        print(f"Got stream info: {ys.url[:50]}...")
        
        output_path = r"D:\song\Final_Music_Official"
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        print("Downloading...")
        filename = ys.download(output_path=output_path, filename="Hearts2Hearts_FOCUS_pytubefix.m4a")
        print(f"Success! Downloaded to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_test()
