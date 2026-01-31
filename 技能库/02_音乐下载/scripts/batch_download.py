import os
import re
import sys
from pathlib import Path
from download_and_tag import download_and_search, clean_filename

def parse_song_list(file_path):
    songs = []
    try:
        # 尝试不同编码读取 yuki_videos.txt
        content = ""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='utf-16') as f:
                    content = f.read()
            except:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
        
        # 匹配格式: Artist - Title [Audio] (VideoID)
        # 或者简单的 Title (VideoID)
        pattern = re.compile(r'(.+?)\s*\(([\w-]{11})\)')
        for line in content.splitlines():
            line = line.strip()
            if not line: continue
            
            match = pattern.search(line)
            if match:
                full_raw = match.group(1).strip()
                # 去掉 [Audio], [Official] 等后缀
                full_title = re.sub(r'\[.*?\]', '', full_raw).strip()
                video_id = match.group(2)
                
                # 如果有 " - " 则拆分 Artist 和 Title
                parts = full_title.split(" - ", 1)
                artist = parts[0].strip() if len(parts) > 1 else "Unknown"
                title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                
                songs.append({
                    "query": f"{artist} {title}",
                    "artist": artist,
                    "title": title,
                    "video_id": video_id,
                    "safe_name": clean_filename(f"{artist}_{title}")
                })
    except Exception as e:
        print(f"❌ 解析列表失败: {e}")
    return songs

def main():
    list_path = r"D:\anti\yuki_videos.txt"
    output_dir = r"D:\song\Final_Music_Official"
    
    print(f"🚀 启动批量下载任务...")
    songs = parse_song_list(list_path)
    print(f"📋 发现 {len(songs)} 首歌曲。")
    
    # 检查已存在的文件
    existing_files = [f.stem for f in Path(output_dir).glob("*.mp3")]
    
    success_count = 0
    skip_count = 0
    
    # 默认只执行前几个进行验证，除非指定全部
    limit = 5 
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        limit = 999
    
    for i, song in enumerate(songs):
        if i >= limit:
            print(f"\n✋ 已达到限制 ({limit}首)，停止下载。使用 --all 参数下载全部。")
            break
            
        print(f"\n--- [{i+1}/{len(songs)}] 处理中: {song['artist']} - {song['title']} ---")
        
        if song['safe_name'] in existing_files:
            print(f"⏭️ 文件已存在，跳过: {song['safe_name']}")
            skip_count += 1
            continue
            
        # 调用下载器 (传递 video_id 作为备选)
        try:
            download_and_search(song['query'], filename=song['safe_name'], video_id=song.get('video_id'))
            success_count += 1
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            
    print(f"\n🏁 任务完成！")
    print(f"✅ 成功下载: {success_count}")
    print(f"⏭️ 跳过已存在: {skip_count}")

if __name__ == "__main__":
    main()
