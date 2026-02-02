#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SoundCloud 下载 Agent
继承现有下载功能，提供对话式交互界面
"""

import os
import sys
import re
import subprocess
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ultra_fast_download import (
    fast_download,
    get_song_title,
    get_cover_url
)
from download_mp3_with_cover import (
    download_mp3_and_cover,
    embed_cover_to_mp3,
    verify_mp3_cover
)


class SoundCloudDownloadAgent:
    """SoundCloud下载Agent - 提供对话式下载服务"""
    
    def __init__(self, output_dir="D:/song"):
        """
        初始化Agent
        
        Args:
            output_dir: 下载文件保存目录
        """
        self.output_dir = output_dir
        self.download_history = []
        self.current_task = None
        
    def is_soundcloud_url(self, url):
        """检查是否为SoundCloud链接"""
        soundcloud_pattern = r'https?://(www\.)?soundcloud\.com/'
        return bool(re.match(soundcloud_pattern, url))
    
    def is_playlist_url(self, url):
        """检查是否为播放列表链接"""
        playlist_patterns = [
            r'/sets/',
            r'/playlists/',
            r'/discover/sets/',
        ]
        return any(re.search(pattern, url) for pattern in playlist_patterns)
    
    def get_playlist_tracks(self, url):
        """获取播放列表中的所有音轨链接"""
        try:
            print("📋 正在获取播放列表信息...")
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--flat-playlist",
                "--print", "%(webpage_url)s",
                "--quiet",
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                print(f"✅ 找到 {len(urls)} 首音轨")
                return urls
            else:
                print(f"⚠️ 获取播放列表失败: {result.stderr[:100]}")
                return []
        except Exception as e:
            print(f"❌ 获取播放列表异常: {e}")
            return []
    
    def extract_url_from_text(self, text):
        """从文本中提取SoundCloud链接"""
        # 匹配完整的 SoundCloud URL（不使用捕获组，避免返回元组）
        url_pattern = r'https?://(?:www\.)?soundcloud\.com/[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, text)
        return matches[0] if matches else None
    
    def get_song_info(self, url):
        """获取歌曲信息"""
        try:
            print("📝 正在获取歌曲信息...")
            title = get_song_title(url)
            cover_url = get_cover_url(url)
            
            info = {
                'title': title,
                'cover_url': cover_url,
                'url': url
            }
            
            print(f"✅ 歌曲标题: {title}")
            if cover_url:
                print(f"✅ 封面URL: {cover_url[:50]}...")
            
            return info
        except Exception as e:
            print(f"❌ 获取信息失败: {e}")
            return None
    
    def download_playlist(self, url, method="fast"):
        """
        下载SoundCloud播放列表中的所有音轨
        
        Args:
            url: SoundCloud播放列表链接
            method: 下载方法 ("fast" 或 "standard")
        
        Returns:
            dict: 下载结果
        """
        if not self.is_soundcloud_url(url):
            return {
                'success': False,
                'message': '❌ 无效的SoundCloud链接',
                'url': url
            }
        
        print(f"\n{'='*60}")
        print(f"📋 开始下载 SoundCloud 播放列表")
        print(f"{'='*60}")
        print(f"🔗 链接: {url}")
        
        # 获取播放列表中的所有音轨
        track_urls = self.get_playlist_tracks(url)
        
        if not track_urls:
            return {
                'success': False,
                'message': '❌ 无法获取播放列表中的音轨，请检查链接是否有效',
                'url': url
            }
        
        print(f"\n📊 播放列表统计: 共 {len(track_urls)} 首音轨")
        print(f"{'='*60}\n")
        
        success_count = 0
        failed_count = 0
        failed_urls = []
        results = []
        
        for i, track_url in enumerate(track_urls, 1):
            print(f"\n[{i}/{len(track_urls)}] 正在下载音轨...")
            print(f"🔗 {track_url}")
            print("-" * 60)
            
            try:
                result = self.download_track(track_url, method)
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
                    print(f"✅ [{i}/{len(track_urls)}] 下载成功")
                else:
                    failed_count += 1
                    failed_urls.append(track_url)
                    print(f"❌ [{i}/{len(track_urls)}] 下载失败: {result.get('message', '未知错误')}")
            except Exception as e:
                failed_count += 1
                failed_urls.append(track_url)
                print(f"❌ [{i}/{len(track_urls)}] 下载异常: {e}")
            
            # 每首音轨之间稍作延迟，避免请求过快
            if i < len(track_urls):
                time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"📊 播放列表下载完成！")
        print(f"✅ 成功: {success_count} 首")
        print(f"❌ 失败: {failed_count} 首")
        print(f"📁 保存位置: {self.output_dir}")
        
        if failed_urls:
            print(f"\n⚠️ 失败的音轨链接 ({len(failed_urls)} 首):")
            for failed_url in failed_urls[:5]:  # 只显示前5个
                print(f"  - {failed_url}")
            if len(failed_urls) > 5:
                print(f"  ... 还有 {len(failed_urls) - 5} 首失败")
        
        return {
            'success': success_count > 0,
            'message': f'✅ 播放列表下载完成: 成功 {success_count} 首，失败 {failed_count} 首',
            'url': url,
            'total': len(track_urls),
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_urls': failed_urls,
            'results': results,
            'output_dir': self.output_dir
        }
    
    def clean_url(self, url):
        """清理URL，去掉查询参数和片段"""
        # 去掉查询参数（?后面的部分）
        clean = url.split('?')[0]
        # 去掉片段（#后面的部分）
        clean = clean.split('#')[0]
        return clean.strip()
    
    def download_track(self, url, method="fast"):
        """
        下载SoundCloud音轨
        
        Args:
            url: SoundCloud链接（支持带查询参数）
            method: 下载方法 ("fast" 或 "standard")
        
        Returns:
            dict: 下载结果
        """
        if not self.is_soundcloud_url(url):
            return {
                'success': False,
                'message': '❌ 无效的SoundCloud链接',
                'url': url
            }
        
        # 检查是否为播放列表
        if self.is_playlist_url(url):
            return self.download_playlist(url, method)
        
        # 清理URL（去掉查询参数）
        clean_url = self.clean_url(url)
        if clean_url != url:
            print(f"🔧 已清理URL参数: {url[:60]}...")
            print(f"   使用链接: {clean_url}")
        
        print(f"\n{'='*60}")
        print(f"🎵 开始下载 SoundCloud 音轨")
        print(f"{'='*60}")
        print(f"🔗 链接: {clean_url}")
        
        self.current_task = {
            'url': clean_url,
            'original_url': url,
            'status': 'downloading',
            'method': method
        }
        
        try:
            if method == "fast":
                # 使用快速下载方法
                success = fast_download(clean_url, self.output_dir)
                
                if success:
                    result = {
                        'success': True,
                        'message': '✅ 下载完成！',
                        'url': clean_url,
                        'original_url': url,
                        'output_dir': self.output_dir
                    }
                else:
                    result = {
                        'success': False,
                        'message': '❌ 下载失败',
                        'url': clean_url,
                        'original_url': url
                    }
            else:
                # 使用标准下载方法
                mp3_path, cover_path = download_mp3_and_cover(clean_url, self.output_dir)
                
                if mp3_path and os.path.exists(mp3_path):
                    # 嵌入封面
                    if cover_path:
                        embed_cover_to_mp3(mp3_path, cover_path)
                        verify_mp3_cover(mp3_path)
                    
                    file_size = os.path.getsize(mp3_path)
                    result = {
                        'success': True,
                        'message': '✅ 下载完成！',
                        'url': clean_url,
                        'original_url': url,
                        'mp3_path': mp3_path,
                        'cover_path': cover_path,
                        'file_size': file_size,
                        'output_dir': self.output_dir
                    }
                else:
                    result = {
                        'success': False,
                        'message': '❌ 下载失败',
                        'url': clean_url,
                        'original_url': url
                    }
            
            # 更新任务状态
            self.current_task['status'] = 'completed' if result['success'] else 'failed'
            self.current_task['result'] = result
            
            # 添加到历史记录
            self.download_history.append(self.current_task.copy())
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'message': f'❌ 下载出错: {str(e)}',
                'url': clean_url,
                'original_url': url,
                'error': str(e)
            }
            self.current_task['status'] = 'error'
            self.current_task['result'] = error_result
            self.download_history.append(self.current_task.copy())
            return error_result
    
    def process_user_input(self, user_input):
        """
        处理用户输入，自动识别下载请求
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            dict: 处理结果
        """
        user_input = user_input.strip()
        
        # 提取URL
        url = self.extract_url_from_text(user_input)
        
        if not url:
            # 检查是否是命令
            if user_input.lower() in ['help', '帮助', 'h']:
                return self.show_help()
            elif user_input.lower() in ['history', '历史', 'his']:
                return self.show_history()
            elif user_input.lower() in ['quit', 'exit', '退出', 'q']:
                return {'action': 'quit', 'message': '👋 再见！'}
            else:
                return {
                    'success': False,
                    'message': '❌ 未找到SoundCloud链接。请提供有效的SoundCloud URL。'
                }
        
        # 检查下载方法
        method = "fast"
        if "standard" in user_input.lower() or "标准" in user_input:
            method = "standard"
        
        # 执行下载
        return self.download_track(url, method)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = f"""
{'='*60}
🎵 SoundCloud 下载 Agent - 帮助
{'='*60}

📋 使用方法:
  1. 直接粘贴 SoundCloud 链接即可开始下载
  2. 支持的命令:
     - help / 帮助 / h      : 显示此帮助信息
     - history / 历史 / his  : 查看下载历史
     - quit / exit / 退出 / q: 退出程序

📥 下载方法:
  - 快速模式 (默认): 并行下载音频和封面，速度更快
  - 标准模式: 使用 "standard" 或 "标准" 关键字启用

📁 保存位置: {self.output_dir}

💡 示例:
  - 直接粘贴链接: https://soundcloud.com/...
  - 标准模式下载: https://soundcloud.com/... standard

{'='*60}
        """
        print(help_text)
        return {'action': 'help', 'message': help_text}
    
    def show_history(self):
        """显示下载历史"""
        if not self.download_history:
            print("📜 暂无下载历史")
            return {'action': 'history', 'message': '暂无下载历史'}
        
        print(f"\n{'='*60}")
        print(f"📜 下载历史 (共 {len(self.download_history)} 条)")
        print(f"{'='*60}")
        
        for i, task in enumerate(self.download_history, 1):
            status_icon = "✅" if task.get('status') == 'completed' else "❌"
            print(f"\n{i}. {status_icon} {task.get('url', 'Unknown')[:60]}...")
            print(f"   状态: {task.get('status', 'unknown')}")
            if task.get('result'):
                print(f"   结果: {task['result'].get('message', 'N/A')}")
        
        print(f"\n{'='*60}\n")
        
        return {
            'action': 'history',
            'count': len(self.download_history),
            'history': self.download_history
        }
    
    def interactive_mode(self):
        """交互式对话模式"""
        print(f"""
{'='*60}
🎵 SoundCloud 下载 Agent
{'='*60}
欢迎使用 SoundCloud 下载助手！

💡 提示:
  - 直接粘贴 SoundCloud 链接即可下载
  - 输入 'help' 查看帮助
  - 输入 'quit' 退出程序

{'='*60}
        """)
        
        while True:
            try:
                user_input = input("\n🎵 请输入 SoundCloud 链接 (或输入命令): ").strip()
                
                if not user_input:
                    continue
                
                result = self.process_user_input(user_input)
                
                if result.get('action') == 'quit':
                    print(result.get('message', '👋 再见！'))
                    break
                
                if result.get('success'):
                    print(f"\n{result.get('message', '')}")
                    if result.get('mp3_path'):
                        print(f"📁 文件位置: {result['mp3_path']}")
                        print(f"📊 文件大小: {result.get('file_size', 0) / 1024 / 1024:.2f} MB")
                else:
                    print(f"\n{result.get('message', '操作失败')}")
                
            except KeyboardInterrupt:
                print("\n\n👋 程序已中断，再见！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SoundCloud 下载 Agent')
    parser.add_argument('url', nargs='?', help='SoundCloud 链接 (可选)')
    parser.add_argument('-o', '--output', default='D:/song', help='输出目录 (默认: D:/song)')
    parser.add_argument('-m', '--method', choices=['fast', 'standard'], default='fast', 
                       help='下载方法 (默认: fast)')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='启动交互式模式')
    
    args = parser.parse_args()
    
    # 创建Agent
    agent = SoundCloudDownloadAgent(output_dir=args.output)
    
    if args.interactive or not args.url:
        # 交互式模式
        agent.interactive_mode()
    else:
        # 直接下载模式
        result = agent.download_track(args.url, args.method)
        if result.get('success'):
            print(f"\n{result.get('message', '')}")
            sys.exit(0)
        else:
            print(f"\n{result.get('message', '下载失败')}")
            sys.exit(1)


if __name__ == "__main__":
    main()















