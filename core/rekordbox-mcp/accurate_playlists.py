#!/usr/bin/env python3
"""
准确的播放列表分析器
"""

import pyrekordbox

def analyze_accurate_playlists():
    print("准确的播放列表分析")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        playlists = db.get_playlist()
        playlists_list = list(playlists)
        print(f"找到 {len(playlists_list)} 个播放列表")
        
        # 重点关注华语和Boiler Room播放列表
        print("\n华语和Boiler Room播放列表分析:")
        print("-" * 50)
        
        # 查找华语播放列表
        chinese_playlists = [p for p in playlists_list if '华语' in p.Name or '中文' in p.Name]
        print(f"\n华语播放列表: {len(chinese_playlists)} 个")
        
        for playlist in chinese_playlists:
            print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_list = list(playlist.Songs)
                    print(f"歌曲数量: {len(songs_list)}")
                    
                    if songs_list:
                        print("前5首歌曲:")
                        for i, song in enumerate(songs_list[:5]):
                            try:
                                if hasattr(song, 'Content') and song.Content:
                                    content = song.Content
                                    title = getattr(content, 'Title', 'Unknown')
                                    artist = getattr(content, 'ArtistName', 'Unknown')
                                    bpm = getattr(content, 'BPM', 0)
                                    key = getattr(content, 'Key', 'Unknown')
                                    
                                    print(f"  {i+1}. {title} - {artist}")
                                    if bpm:
                                        print(f"     BPM: {bpm}")
                                    if key:
                                        print(f"     调性: {key}")
                            except Exception as e:
                                print(f"  {i+1}. 获取歌曲详情失败: {e}")
                else:
                    print("无法访问歌曲列表")
            except Exception as e:
                print(f"获取歌曲失败: {e}")
        
        # 查找Boiler Room播放列表
        boiler_playlists = [p for p in playlists_list if 'Boiler' in p.Name]
        print(f"\nBoiler Room播放列表: {len(boiler_playlists)} 个")
        
        for playlist in boiler_playlists:
            print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_list = list(playlist.Songs)
                    print(f"歌曲数量: {len(songs_list)}")
                    
                    if songs_list:
                        print("前5首歌曲:")
                        for i, song in enumerate(songs_list[:5]):
                            try:
                                if hasattr(song, 'Content') and song.Content:
                                    content = song.Content
                                    title = getattr(content, 'Title', 'Unknown')
                                    artist = getattr(content, 'ArtistName', 'Unknown')
                                    bpm = getattr(content, 'BPM', 0)
                                    key = getattr(content, 'Key', 'Unknown')
                                    
                                    print(f"  {i+1}. {title} - {artist}")
                                    if bpm:
                                        print(f"     BPM: {bpm}")
                                    if key:
                                        print(f"     调性: {key}")
                            except Exception as e:
                                print(f"  {i+1}. 获取歌曲详情失败: {e}")
                else:
                    print("无法访问歌曲列表")
            except Exception as e:
                print(f"获取歌曲失败: {e}")
        
        # 显示所有播放列表的准确统计
        print("\n所有播放列表统计:")
        print("-" * 40)
        
        for playlist in playlists_list:
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_count = len(list(playlist.Songs))
                    print(f"{playlist.Name}: {songs_count} 首歌曲")
                else:
                    print(f"{playlist.Name}: 无法访问歌曲")
            except:
                print(f"{playlist.Name}: 错误")
        
        print("\n播放列表分析完成!")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = analyze_accurate_playlists()
    if success:
        print("\n播放列表分析成功!")
    else:
        print("\n播放列表分析失败!")










