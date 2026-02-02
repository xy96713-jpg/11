#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载MP3格式音乐并嵌入原始封面
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON
    from mutagen.mp4 import MP4
    from PIL import Image
except ImportError as e:
    print(f"错误：缺少必要的库 - {e}")
    print("请运行：pip install mutagen pillow requests")
    exit(1)

def safe_print(text):
    """安全打印，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def check_ytdlp():
    """检查yt-dlp是否安装"""
    try:
        result = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            safe_print(f"yt-dlp版本: {version}")
            return True
        else:
            safe_print("yt-dlp未正确安装")
            return False
    except Exception as e:
        safe_print(f"检查yt-dlp时出错: {e}")
        return False

def download_mp3_and_cover(url, output_dir="D:/歌"):
    """下载MP3格式音乐和封面"""
    try:
        safe_print("🎵 MCP音乐下载器 - MP3版本")
        safe_print("=" * 50)
        
        # 检查yt-dlp
        if not check_ytdlp():
            safe_print("正在安装yt-dlp...")
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频信息
        safe_print("获取视频信息...")
        info_cmd = [
            sys.executable, "-m", "yt_dlp", 
            "--dump-json", 
            "--no-download",
            url
        ]
        
        result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            safe_print(f"获取信息失败: {result.stderr}")
            return None, None
        
        import json
        info = json.loads(result.stdout)
        title = info.get('title', 'Unknown')
        artist = info.get('uploader', 'Unknown')
        duration = info.get('duration', 0)
        
        safe_print(f"标题: {title}")
        safe_print(f"艺术家: {artist}")
        safe_print(f"时长: {duration:.1f}秒")
        
        # 获取封面URL
        thumbnails = info.get('thumbnails', [])
        cover_url = None
        for thumb in thumbnails:
            if thumb.get('id') == 'original':
                cover_url = thumb.get('url')
                break
        
        if not cover_url:
            # 如果没有original，使用最大的
            cover_url = info.get('thumbnail')
        
        safe_print(f"封面URL: {cover_url}")
        
        # 下载MP3格式音频（尝试多种格式）
        safe_print("正在下载音频...")
        
        # 尝试多种格式
        formats = [
            "http_mp3_1_0",  # HTTP MP3格式
            "hls_mp3_1_0",  # HLS MP3格式
            "bestaudio[ext=mp3]/bestaudio",  # 最佳MP3音频
        ]
        
        audio_result = None
        for fmt in formats:
            audio_cmd = [
                sys.executable, "-m", "yt_dlp",
                "--format", fmt,
                "--output", f"{output_dir}/%(title)s.%(ext)s",
                url
            ]
            
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                audio_result = result
                safe_print(f"使用格式 {fmt} 下载成功")
                break
            else:
                safe_print(f"格式 {fmt} 不可用，尝试下一个...")
        
        if not audio_result or audio_result.returncode != 0:
            safe_print(f"所有格式尝试失败: {result.stderr if 'result' in locals() else '未知错误'}")
            return None, None
        
        # 查找下载的MP3文件
        mp3_files = list(Path(output_dir).glob("*.mp3"))
        if not mp3_files:
            safe_print("未找到下载的MP3文件")
            return None, None
        
        # 获取最新的MP3文件
        latest_mp3 = max(mp3_files, key=lambda x: x.stat().st_mtime)
        safe_print(f"下载的MP3文件: {latest_mp3.name}")
        
        # 下载封面
        cover_path = None
        if cover_url:
            safe_print("正在下载封面...")
            try:
                response = requests.get(cover_url, timeout=30)
                response.raise_for_status()
                
                # 确定封面文件扩展名
                if cover_url.endswith('.png'):
                    cover_ext = '.png'
                else:
                    cover_ext = '.jpg'
                
                cover_path = latest_mp3.with_suffix(cover_ext)
                with open(cover_path, 'wb') as f:
                    f.write(response.content)
                
                safe_print(f"封面下载成功: {cover_path.name}")
                
            except Exception as e:
                safe_print(f"下载封面失败: {e}")
                cover_path = None
        
        return str(latest_mp3), str(cover_path) if cover_path else None
        
    except Exception as e:
        safe_print(f"下载过程中出错: {e}")
        return None, None

def embed_cover_to_mp3(mp3_path, cover_path):
    """将封面嵌入到MP3文件"""
    try:
        if not cover_path or not os.path.exists(cover_path):
            safe_print("封面文件不存在，跳过嵌入")
            return False
        
        safe_print(f"正在将封面嵌入到: {os.path.basename(mp3_path)}")
        
        # 读取MP3文件
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        
        # 读取封面数据
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # 确定MIME类型
        img = Image.open(cover_path)
        mime_type = 'image/png' if img.format == 'PNG' else 'image/jpeg'
        
        # 删除现有封面标签
        keys_to_remove = [key for key in audio.tags.keys() if key.startswith('APIC')]
        for key in keys_to_remove:
            del audio.tags[key]
        
        # 添加新封面标签
        audio.tags.add(APIC(
            encoding=3, mime=mime_type, type=3, 
            desc='Cover (front)', data=cover_data
        ))
        
        # 保存文件
        audio.tags.version = (2, 3, 0)
        audio.save(mp3_path, v2_version=3)
        
        safe_print(f"✅ 封面已成功嵌入!")
        return True
        
    except Exception as e:
        safe_print(f"嵌入封面时出错: {e}")
        return False

def verify_mp3_cover(mp3_path):
    """验证MP3文件的封面嵌入"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags:
            cover_found = any(key.startswith('APIC') for key in audio.tags.keys())
            if cover_found:
                safe_print("✅ 封面验证成功!")
                return True
            else:
                safe_print("❌ 未找到封面标签")
                return False
        else:
            safe_print("❌ 无ID3标签")
            return False
    except Exception as e:
        safe_print(f"验证时出错: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        safe_print("用法: python download_mp3_with_cover.py <音乐链接>")
        return
    
    url = sys.argv[1]
    
    # 下载MP3和封面
    mp3_path, cover_path = download_mp3_and_cover(url)
    
    if mp3_path and os.path.exists(mp3_path):
        safe_print(f"✅ 下载完成: {os.path.basename(mp3_path)}")
        
        # 嵌入封面
        if cover_path:
            embed_cover_to_mp3(mp3_path, cover_path)
        
        # 显示文件信息
        file_size = os.path.getsize(mp3_path)
        safe_print(f"文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
        
        safe_print("\n🎉 完成! 封面已自动嵌入，现在可以在Windows文件管理器中看到缩略图了!")
        
    else:
        safe_print("❌ 下载失败")

if __name__ == "__main__":
    main()



