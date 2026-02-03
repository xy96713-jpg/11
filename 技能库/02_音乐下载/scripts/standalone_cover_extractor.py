#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Cover Extractor for Skill 02
Supports extracting covers from URLs (YouTube, SoundCloud, etc.) or local MP3/M4A files.
"""

import os
import sys
import subprocess
import requests
import re
from pathlib import Path

import difflib
import shutil

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen.mp4 import MP4, MP4Cover
    from PIL import Image
except ImportError:
    print("[*] Installing missing dependencies: mutagen, pillow...")
    subprocess.run([sys.executable, "-m", "pip", "install", "mutagen", "pillow"], check=True)
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen.mp4 import MP4, MP4Cover
    from PIL import Image

def find_local_match(query, search_dir):
    """在本地目录模糊搜索匹配的文件"""
    print(f"[*] Searching locally in {search_dir} for: {query}")
    query_l = query.lower()
    
    # 获取音频文件和图片文件
    all_files = os.listdir(search_dir)
    audio_files = [f for f in all_files if f.lower().endswith(('.mp3', '.m4a', '.wav', '.flac'))]
    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    # 1. 优先尝试直接在图片文件中寻找 (侧边栏封面)
    img_matches = [f for f in image_files if query_l in f.lower()]
    if img_matches:
        # 返回最匹配的图片
        return os.path.join(search_dir, sorted(img_matches, key=len)[0])

    # 2. 尝试包含匹配的音频文件
    audio_matches = [f for f in audio_files if query_l in f.lower()]
    if audio_matches:
        return os.path.join(search_dir, sorted(audio_matches, key=len)[0])
    
    # 3. 备选：模糊匹配
    close_matches = difflib.get_close_matches(query_l, audio_files, n=1, cutoff=0.7)
    if close_matches:
        return os.path.join(search_dir, close_matches[0])
    
    return None

def get_cover_from_itunes(query, output_path):
    """从 iTunes 获取高清封面"""
    print(f"[*] Searching iTunes for: {query}")
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['resultCount'] > 0:
            result = data['results'][0]
            # 获取 1000x1000 的高清图
            cover_url = result['artworkUrl100'].replace('100x100bb.jpg', '1000x1000bb.jpg')
            print(f"[*] Found iTunes cover: {cover_url}")
            
            img_data = requests.get(cover_url, timeout=10).content
            final_name = Path(output_path).with_suffix(".jpg")
            with open(final_name, "wb") as f:
                f.write(img_data)
            print(f"✅ iTunes cover saved to: {final_name}")
            return str(final_name)
    except Exception as e:
        print(f"❌ iTunes search failed: {e}")
    return None

def get_cover_from_url(url, output_path, is_query=False):
    """使用 yt-dlp 抓取封图或搜索抓取"""
    print(f"[*] Processing cover target: {url}")
    try:
        # 如果是关键词，使用 ytsearch1:
        search_target = f"ytsearch1:{url}" if is_query else url
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--output", output_path,
            search_target
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # yt-dlp 通常会生成 .jpg 或 .webp，或者带有 .fXXX 的临时后缀
            # 搜索生成的图片
            search_pattern = f"{output_path}*"
            possible_files = list(Path(os.path.dirname(output_path)).glob(f"{Path(output_path).name}*"))
            
            for f in possible_files:
                if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    # 统一重命名为最终的 .jpg
                    final_name = Path(output_path).with_suffix(".jpg")
                    if f != final_name:
                        if final_name.exists():
                            os.remove(final_name)
                        os.rename(f, final_name)
                    print(f"✅ Cover saved to: {final_name}")
                    return str(final_name)
        else:
            print(f"❌ yt-dlp failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error fetching URL cover: {e}")
    return None

def get_cover_from_local_file(file_path, output_base=None):
    """从本地音频提取封图，保留原始后缀"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None

    print(f"[*] Extracting cover from local file: {file_path.name}")
    
    # 1. 查找是否有同名的 _cover.png 或 .jpg 等侧边栏文件
    # 这是最优先级，通常是用户准备好的高清原图
    potential_covers = [
        file_path.with_name(file_path.stem + "_cover.png"),
        file_path.with_name(file_path.stem + "_cover.jpg"),
        file_path.with_name(file_path.stem + "_cover.jpeg"),
        file_path.with_suffix(".png"),
        file_path.with_suffix(".jpg")
    ]
    for pc in potential_covers:
        if pc.exists() and pc.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            # 如果提供了 output_base，则使用 output_base + 原始后缀
            if output_base:
                final_output = Path(output_base).with_suffix(pc.suffix)
            else:
                final_output = pc # 默认就地
            
            print(f"✅ Found sidecar cover: {pc.name} -> {final_output.name}")
            shutil.copy2(pc, final_output)
            return str(final_output)

    # 2. 如果没有侧边栏文件，尝试从音频内部提取 (默认提取为 .jpg)
    output_jpg = Path(output_base).with_suffix(".jpg") if output_base else file_path.with_suffix(".jpg")
    try:
        if file_path.suffix.lower() == ".mp3":
            audio = MP3(file_path, ID3=ID3)
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    with open(output_jpg, "wb") as f:
                        f.write(tag.data)
                    print(f"✅ MP3 Internal Cover extracted to: {output_jpg.name}")
                    return str(output_jpg)
        elif file_path.suffix.lower() == ".m4a":
            audio = MP4(file_path)
            if "covr" in audio.tags:
                cover_data = audio.tags["covr"][0]
                with open(output_jpg, "wb") as f:
                    f.write(cover_data)
                print(f"✅ M4A Internal Cover extracted to: {output_jpg.name}")
                return str(output_jpg)
    except Exception as e:
        print(f"❌ Extraction error for {file_path.name}: {e}")
    return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Standalone Cover Extractor")
    parser.add_argument("target", help="URL or Local File Path or Song Name")
    parser.add_argument("--output", help="Custom output directory")
    
    args = parser.parse_args()
    target = args.target
    
    # 确定输出目录
    target_dir = args.output if args.output else os.getcwd()
    os.makedirs(target_dir, exist_ok=True)
    
    # 默认本地搜索目录
    local_music_dirs = [r"D:\song", r"D:\song\kpop", r"D:\song\kpop house"]
    
    if target.startswith("http"):
        # 直接 URL 下载
        output_base = os.path.join(target_dir, "cover_result")
        get_cover_from_url(target, output_base)
    elif os.path.exists(target):
        # 处理显式提供的本地文件路径
        # 这里提取时也要保留原始后缀的逻辑
        get_cover_from_local_file(target, output_base=os.path.join(target_dir, Path(target).stem))
    else:
        # 关键词搜索：优先本地，后 iTunes，最后 YouTube
        # 清理非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', target)
        output_base = os.path.join(target_dir, safe_name)
        
        # 1. 在多个目录中搜索匹配
        local_path = None
        for d in local_music_dirs:
            if os.path.exists(d):
                local_path = find_local_match(target, d)
                if local_path:
                    break
        
        if local_path:
            print(f"✨ Found local match: {local_path}")
            if get_cover_from_local_file(local_path, output_base=output_base):
                return

        # 2. 尝试 iTunes
        success = get_cover_from_itunes(target, output_base)
        if not success:
            # 3. 备选 YouTube
            get_cover_from_url(target, output_base, is_query=True)

if __name__ == "__main__":
    main()
