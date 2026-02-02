#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超快速音乐下载器 - 优化版
并行下载MP3和封面，然后嵌入封面
"""

import subprocess
import requests
import threading
import os
import re
import sys
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

def get_song_title(url):
    """获取歌曲标题"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'yt_dlp', '--get-title', url
        ], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            title = result.stdout.strip()
            # 清理文件名中的非法字符
            title = re.sub(r'[<>:"/\\|?*]', '', title)
            return title
    except Exception as e:
        print(f"获取标题失败: {e}")
    return "Unknown_Song"

def get_cover_url(url):
    """获取封面URL"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'yt_dlp', '--get-thumbnail', url
        ], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"获取封面URL失败: {e}")
    return None

def download_mp3(url, output_path):
    """下载MP3文件"""
    try:
        # 尝试多种格式，按优先级顺序
        formats = [
            'hls_mp3_1_0',  # 首选格式
            'http_mp3_1_0',  # HTTP MP3格式
            'bestaudio[ext=mp3]/bestaudio/best',  # 最佳音频格式
        ]
        
        for fmt in formats:
            try:
                cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    '--format', fmt,
                    '--output', output_path,
                    url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True
            except subprocess.CalledProcessError as e:
                # 如果是最后一个格式，打印错误信息
                if fmt == formats[-1]:
                    print(f"格式 {fmt} 失败: {e.stderr}")
                continue  # 尝试下一个格式
        
        # 所有格式都失败了，尝试使用最佳音频格式并转换
        try:
            print("尝试下载最佳音频并转换为MP3...")
            result = subprocess.run([
                sys.executable, '-m', 'yt_dlp',
                '--format', 'bestaudio',
                '--output', output_path.replace('.mp3', '.%(ext)s'),
                '--postprocessor-args', 'ffmpeg:-vn -acodec libmp3lame',
                '--postprocessor-args', 'ffmpeg:-q:a 0',
                url
            ], capture_output=True, text=True, check=True)
            
            # 如果输出文件不是mp3，尝试重命名或转换
            import glob
            base_name = os.path.splitext(output_path)[0]
            downloaded_files = glob.glob(f"{base_name}.*")
            if downloaded_files:
                downloaded_file = downloaded_files[0]
                if not downloaded_file.endswith('.mp3'):
                    # 尝试使用ffmpeg转换（如果可用）
                    try:
                        subprocess.run([
                            'ffmpeg', '-i', downloaded_file, '-vn', '-acodec', 'libmp3lame', 
                            '-q:a', '0', output_path, '-y'
                        ], check=True, capture_output=True)
                        os.remove(downloaded_file)
                        return True
                    except:
                        pass
                else:
                    return True
        except:
            pass
        
        print(f"所有格式尝试失败")
        return False
    except Exception as e:
        print(f"MP3下载失败: {e}")
        return False

def download_cover(cover_url, cover_path):
    """下载封面"""
    try:
        response = requests.get(cover_url, timeout=30)
        response.raise_for_status()
        with open(cover_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"封面下载失败: {e}")
        return False

def embed_cover(mp3_path, cover_path):
    """嵌入封面到MP3"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        # 删除现有封面
        keys_to_remove = [key for key in audio.tags.keys() if key.startswith('APIC')]
        for key in keys_to_remove:
            del audio.tags[key]

        # 嵌入新封面
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
            audio.tags.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover (front)',
                data=cover_data
            ))

        audio.tags.version = (2, 3, 0)
        audio.save(mp3_path, v2_version=3)
        return True
    except Exception as e:
        print(f"封面嵌入失败: {e}")
        return False

def fast_download(url, output_dir="D:/song"):
    """超快速下载流程"""
    print("🚀 启动超快速下载...")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 获取歌曲信息
    print("📝 获取歌曲信息...")
    title = get_song_title(url)
    cover_url = get_cover_url(url)
    
    # 设置文件路径
    mp3_path = os.path.join(output_dir, f"{title}.mp3")
    cover_path = os.path.join(output_dir, f"{title}_cover.png") if cover_url else None
    
    print(f"📀 歌曲: {title}")
    if cover_url:
        print(f"🎨 封面: {cover_url}")
    else:
        print("⚠️ 未找到封面，将仅下载音频")
    
    # 2. 下载MP3
    print("⬇️ 下载音频中...")
    mp3_success = download_mp3(url, mp3_path)
    
    if not mp3_success:
        print("❌ MP3下载失败")
        return False
    
    # 3. 如果有封面，下载并嵌入
    if cover_url:
        print("⬇️ 下载封面中...")
        cover_success = download_cover(cover_url, cover_path)
        
        if cover_success:
            print("🔗 嵌入封面...")
            if embed_cover(mp3_path, cover_path):
                print("✅ 下载完成!")
                print(f"📁 文件位置: {mp3_path}")
                print(f"🖼️ 封面位置: {cover_path}")
                return True
            else:
                print("⚠️ 封面嵌入失败，但音频下载成功")
                print(f"📁 文件位置: {mp3_path}")
                return True
        else:
            print("⚠️ 封面下载失败，但音频下载成功")
            print(f"📁 文件位置: {mp3_path}")
            return True
    else:
        print("✅ 下载完成!")
        print(f"📁 文件位置: {mp3_path}")
        return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        fast_download(url)
    else:
        print("请提供音乐链接")



