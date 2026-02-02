import subprocess
import sys
import os

def download_spotify(url, output_dir=r"D:\song"):
    """
    使用 spotdl 下载 Spotify 歌曲，但强制使用 SoundCloud 和 Bandcamp 作为音源。
    """
    print(f"🚀 启动 Spotify 高保真下载器 (V8.7)...")
    print(f"🔗 URL: {url}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # [V8.7] 核心指令: 屏蔽 YouTube，仅使用 SC 和 Bandcamp
    # 使用 sys.executable -m spotdl 确保调用正确的 Python 环境
    try:
        cmd = [
            sys.executable, "-m", "spotdl",
            url,
            "--audio", "soundcloud", "bandcamp",
            "--format", "mp3",
            "--output", output_dir
        ]
        
        print(f"🛠️ 执行指令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"✅ Spotify 歌曲下载并完形成功！")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ spotDL 执行失败: {e}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spotify_agent.py [Spotify_URL]")
        sys.exit(1)
        
    spotify_url = sys.argv[1]
    download_spotify(spotify_url)
