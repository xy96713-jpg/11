#!/usr/bin/env python3
"""
验证真实歌曲 - 只显示确实存在的数据
"""

import asyncio
from pathlib import Path
import sys

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

async def verify_real_songs():
    print("验证华语播放列表中的真实歌曲")
    print("=" * 50)
    
    try:
        # 导入rekordbox-mcp数据库类
        from rekordbox_mcp.database import RekordboxDatabase
        
        # 初始化数据库连接
        print("正在连接Rekordbox数据库...")
        db = RekordboxDatabase()
        await db.connect()
        print("数据库连接成功!")
        
        # 获取华语播放列表
        playlists = await db.get_playlists()
        chinese_playlists = [p for p in playlists if '华语' in p.name]
        
        if not chinese_playlists:
            print("未找到华语播放列表")
            return False
        
        print(f"找到 {len(chinese_playlists)} 个华语播放列表")
        
        # 分析华语播放列表
        for playlist in chinese_playlists:
            print(f"\n播放列表: {playlist.name}")
            print(f"ID: {playlist.id}")
            
            # 获取播放列表中的歌曲
            tracks = await db.get_playlist_tracks(playlist.id)
            print(f"歌曲数量: {len(tracks)}")
            
            if tracks:
                print(f"\n所有歌曲列表:")
                for i, track in enumerate(tracks):
                    print(f"  {i+1:3d}. {track.title} - {track.artist}")
                    if track.bpm:
                        print(f"       BPM: {track.bpm}")
                    if track.key:
                        print(f"       调性: {track.key}")
                    print()
            else:
                print("播放列表为空")
        
        print("\n验证完成")
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False
    
    return True

async def main():
    success = await verify_real_songs()
    if success:
        print("\n歌曲验证成功!")
    else:
        print("\n歌曲验证失败!")

if __name__ == "__main__":
    asyncio.run(main())










