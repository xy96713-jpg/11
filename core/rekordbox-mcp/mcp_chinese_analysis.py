#!/usr/bin/env python3
"""
使用rekordbox-mcp MCP工具分析华语播放列表
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 导入rekordbox-mcp模块
try:
    from rekordbox_mcp.server import (
        get_playlists,
        get_playlist_tracks,
        search_tracks,
        analyze_library,
        get_library_stats
    )
    from rekordbox_mcp.database import RekordboxDatabase
except ImportError as e:
    print(f"导入rekordbox-mcp模块失败: {e}")
    print("请确保rekordbox-mcp已正确安装")
    sys.exit(1)

async def mcp_chinese_analysis():
    print("使用rekordbox-mcp MCP工具分析华语播放列表")
    print("=" * 60)
    
    try:
        # 初始化数据库连接
        print("正在连接Rekordbox数据库...")
        db = RekordboxDatabase()
        await db.connect()
        print("数据库连接成功!")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        playlists = await get_playlists()
        print(f"找到 {len(playlists)} 个播放列表")
        
        # 查找华语播放列表
        chinese_playlists = [p for p in playlists if '华语' in p.get('name', '')]
        print(f"找到 {len(chinese_playlists)} 个华语播放列表")
        
        if not chinese_playlists:
            print("未找到华语播放列表")
            return False
        
        # 分析每个华语播放列表
        for playlist in chinese_playlists:
            print(f"\n分析播放列表: {playlist.get('name', 'Unknown')}")
            print(f"ID: {playlist.get('id', 'Unknown')}")
            
            # 获取播放列表中的歌曲
            try:
                tracks = await get_playlist_tracks(playlist['id'])
                print(f"歌曲数量: {len(tracks)}")
                
                if tracks:
                    print(f"\n前10首歌曲:")
                    for i, track in enumerate(tracks[:10]):
                        print(f"  {i+1:2d}. {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")
                        if track.get('bpm'):
                            print(f"      BPM: {track['bpm']}")
                        if track.get('key'):
                            print(f"      调性: {track['key']}")
                        print()
                    
                    # 分析BPM
                    bpms = [t.get('bpm') for t in tracks if t.get('bpm') and t['bpm'] > 0]
                    if bpms:
                        print(f"BPM分析:")
                        print(f"  平均BPM: {sum(bpms) / len(bpms):.1f}")
                        print(f"  最低BPM: {min(bpms):.1f}")
                        print(f"  最高BPM: {max(bpms):.1f}")
                    
                    # 分析艺术家
                    artists = [t.get('artist') for t in tracks if t.get('artist') and t['artist'] != 'Unknown']
                    if artists:
                        artist_counts = {}
                        for artist in artists:
                            artist_counts[artist] = artist_counts.get(artist, 0) + 1
                        
                        sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
                        print(f"\n艺术家统计:")
                        for artist, count in sorted_artists[:10]:
                            print(f"  {artist}: {count} 首")
                
            except Exception as e:
                print(f"获取播放列表歌曲失败: {e}")
        
        # 使用MCP工具进行库分析
        print(f"\n使用MCP工具进行库分析...")
        try:
            # 按艺术家分析
            artist_analysis = await analyze_library(
                group_by="artist",
                aggregate_by="count",
                top_n=10
            )
            print(f"艺术家分析结果: {json.dumps(artist_analysis, indent=2, ensure_ascii=False)}")
            
            # 按BPM分析
            bpm_analysis = await analyze_library(
                group_by="bpm",
                aggregate_by="count",
                top_n=10
            )
            print(f"BPM分析结果: {json.dumps(bpm_analysis, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"MCP库分析失败: {e}")
        
        # 获取库统计信息
        try:
            stats = await get_library_stats()
            print(f"\n库统计信息:")
            print(f"总歌曲数: {stats.get('total_tracks', 'Unknown')}")
            print(f"总播放列表数: {stats.get('total_playlists', 'Unknown')}")
            print(f"平均BPM: {stats.get('average_bpm', 'Unknown')}")
            
        except Exception as e:
            print(f"获取库统计失败: {e}")
        
        print("\nMCP分析完成!")
        
    except Exception as e:
        print(f"MCP分析失败: {e}")
        return False
    
    return True

async def main():
    success = await mcp_chinese_analysis()
    if success:
        print("\n华语歌曲MCP分析成功!")
    else:
        print("\n华语歌曲MCP分析失败!")

if __name__ == "__main__":
    asyncio.run(main())










