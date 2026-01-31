import asyncio
import httpx
import re
import json
import argparse
import sys
import subprocess
import shutil
import os

class DouyinParser:
    def __init__(self, cookie_path=None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        self.cookie_path = cookie_path
        if cookie_path and os.path.exists(cookie_path):
            with open(cookie_path, 'r', encoding='utf-8') as f:
                self.headers["Cookie"] = f.read().strip()
                print(f"[*] Loaded cookies from {cookie_path}", file=sys.stderr)

    async def get_redirect_url(self, url):
        """处理短链接追踪重定向，模拟移动端或桌面浏览器以获取完整长链"""
        # 如果是短链格式 https://v.douyin.com/abc/，尝试直接提取 ID 的一种可能：
        # 很多时候重定向失败是因为 UA，但我们也可以直接把原始短链喂给 yt-dlp，它其实内置了更好的解析。
        return url

    async def get_video_id(self, url):
        # 只有在 Web API 模式下才需要 ID
        # 如果是短链，我们必须重定向一次获取 ID
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10) as client:
            try:
                response = await client.get(url)
                final_url = str(response.url)
            except Exception:
                final_url = url

        match = re.search(r'video/(\d+)', final_url) or re.search(r'modal_id=(\d+)', final_url)
        if match:
            return match.group(1)
        
        return None

    async def parse_via_ytdlp(self, url):
        """用 yt-dlp 作为备选方案绕过反爬"""
        # 硬编码可能存在的路径
        ytdlp_path = shutil.which("yt-dlp") or r"C:\Users\Administrator\AppData\Roaming\Python\Python312\Scripts\yt-dlp.exe"
        
        if not os.path.exists(ytdlp_path) and not shutil.which("yt-dlp"):
            return {"error": f"系统未找到 yt-dlp (尝试路径: {ytdlp_path})"}
            
        try:
            print(f"[*] Executing yt-dlp at: {ytdlp_path}", file=sys.stderr)
            process = await asyncio.create_subprocess_exec(
                ytdlp_path, "-j", "--no-check-certificate", url,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                err_msg = stderr.decode().strip()
                print(f"[*] yt-dlp stderr: {err_msg}", file=sys.stderr)
                return {"error": f"yt-dlp 解析失败 (Code {process.returncode}): {err_msg[:200]}"}
            
            data = json.loads(stdout.decode())
            return {
                "title": data.get("title") or data.get("description") or "无标题",
                "author": {
                    "nickname": data.get("uploader", "未知作者"),
                    "signature": "",
                    "uid": data.get("uploader_id", "")
                },
                "video_url": data.get("url"),
                "cover_url": data.get("thumbnail"),
                "music": {
                    "title": data.get("track", "未知音乐"),
                    "author": data.get("artist", "未知歌手")
                },
                "stats": {
                    "digg_count": data.get("like_count", 0),
                    "comment_count": data.get("comment_count", 0),
                    "play_count": data.get("view_count", 0)
                },
                "source": "yt-dlp"
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"yt-dlp 过程出错 ({type(e).__name__}): {str(e)}"}

    async def parse(self, url):
        # 1. 尝试 Web API
        result = await self._parse_web_api(url)
        
        # 2. 如果失败，尝试 yt-dlp
        if "error" in result:
            print(f"[*] Web API 失败: {result['error']}，切换至 yt-dlp...", file=sys.stderr)
            result = await self.parse_via_ytdlp(url)
            
        return result

    async def _parse_web_api(self, url):
        video_id = await self.get_video_id(url)
        if not video_id:
            return {"error": "无法从链接中提取视频 ID"}

        # 测试多个可能的 API 组合
        test_configs = [
            {"aid": "6383", "platform": "webapp"},
            {"aid": "1128", "platform": "android"},
            {"aid": "1128", "platform": "iphone"}
        ]
        
        for config in test_configs:
            print(f"[*] Trying API config: {config}", file=sys.stderr)
            api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}&device_platform={config['platform']}&aid={config['aid']}"
            
            async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
                try:
                    response = await client.get(api_url)
                    if response.status_code != 200:
                        continue
                        
                    data = response.json()
                    item_list = data.get("item_list") or ([data.get("aweme_detail")] if data.get("aweme_detail") else None)
                    
                    if not item_list:
                        continue

                    # 发现有效数据，结束循环
                    item = item_list[0]
                    video_data = item.get("video", {})
                    url_list = video_data.get("play_addr", {}).get("url_list", [])
                    
                    if not url_list:
                        continue

                    no_wm_url = url_list[0].replace("playwm", "play")
                    
                    # HEAD 追踪真实 CDN (增加自定义 UA 以防拦截)
                    mob_headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"}
                    async with httpx.AsyncClient(headers=mob_headers, follow_redirects=True) as client_dl:
                        dl_res = await client_dl.head(no_wm_url)
                        final_url = str(dl_res.url)

                    return {
                        "title": item.get("desc", "无标题"),
                        "author": {
                            "nickname": item.get("author", {}).get("nickname", "未知"),
                            "signature": item.get("author", {}).get("signature", ""),
                            "uid": item.get("author", {}).get("uid", "")
                        },
                        "video_url": final_url,
                        "cover_url": video_data.get("cover", {}).get("url_list", [""])[0],
                        "music": {
                            "title": item.get("music", {}).get("title", "未知"),
                            "author": item.get("music", {}).get("author", "未知")
                        },
                        "stats": item.get("statistics", {}),
                        "source": f"web_api_{config['platform']}"
                    }
                except Exception as e:
                    print(f"[*] Config {config} failed: {e}", file=sys.stderr)
                    continue

        return {"error": "尝试了所有已知 Web API 接口，均被封锁。建议提供有效 Cookie 或长链接。"}

async def main():
    parser = argparse.ArgumentParser(description="抖音智能解析核心 (Antigravity V6.0)")
    parser.add_argument("--url", required=True, help="抖音分享链接")
    parser.add_argument("--summary", action="store_true", help="是否执行内容分析总结")
    parser.add_argument("--cookies", help="包含抖音 Cookie 的文本文件路径")
    args = parser.parse_args()

    douyin = DouyinParser(cookie_path=args.cookies)
    result = await douyin.parse(args.url)
    
    if "error" not in result and args.summary:
        from core_analyzer import VideoContentAnalyzer
        print("[*] 正在启动“最强大脑”视频内容分析模块...", file=sys.stderr)
        analyzer = VideoContentAnalyzer()
        summary = await analyzer.summarize(result["video_url"], result)
        result["summary"] = summary

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
