#!/usr/bin/env python3
"""
详细读取Rekordbox播放列表
"""

import pyrekordbox

def read_detailed_playlists():
    print("详细读取Rekordbox播放列表")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        playlists = db.get_playlist()
        playlists_list = list(playlists)
        print(f"找到 {len(playlists_list)} 个播放列表")
        
        if playlists_list:
            print("\n所有播放列表:")
            print("-" * 60)
            
            for i, playlist in enumerate(playlists_list):
                print(f"{i+1:2d}. {playlist.Name}")
                print(f"    ID: {playlist.ID}")
                
                # 获取播放列表属性
                try:
                    attrs = [attr for attr in dir(playlist) if not attr.startswith('_')]
                    print(f"    可用属性: {', '.join(attrs[:10])}...")  # 只显示前10个属性
                except:
                    pass
                
                # 尝试获取歌曲数量
                try:
                    songs = db.get_playlist_songs(playlist.ID)
                    songs_list = list(songs)
                    print(f"    歌曲数量: {len(songs_list)}")
                    
                    # 显示前3首歌曲
                    if songs_list:
                        print("    前3首歌曲:")
                        for j, song in enumerate(songs_list[:3]):
                            print(f"      {j+1}. {song.Title} - {song.ArtistName}")
                            if hasattr(song, 'BPM') and song.BPM:
                                print(f"         BPM: {song.BPM}")
                            if hasattr(song, 'Key') and song.Key:
                                print(f"         调性: {song.Key}")
                except Exception as e:
                    print(f"    获取歌曲失败: {e}")
                
                print()
        
        # 特别关注一些常见的播放列表类型
        print("\n查找特定类型的播放列表:")
        print("-" * 40)
        
        # 查找包含特定关键词的播放列表
        keywords = ['Boiler', 'Electronic', 'Techno', 'House', 'Deep', 'Acid', '华语', '中文', 'K-Pop', 'J-Pop']
        
        for keyword in keywords:
            matching_playlists = [p for p in playlists_list if keyword.lower() in p.Name.lower()]
            if matching_playlists:
                print(f"\n包含 '{keyword}' 的播放列表:")
                for playlist in matching_playlists:
                    print(f"  - {playlist.Name} (ID: {playlist.ID})")
                    
                    # 获取这些播放列表的歌曲
                    try:
                        songs = db.get_playlist_songs(playlist.ID)
                        songs_list = list(songs)
                        print(f"    歌曲数量: {len(songs_list)}")
                        
                        if songs_list:
                            print("    歌曲示例:")
                            for song in songs_list[:3]:
                                print(f"      * {song.Title} - {song.ArtistName}")
                    except Exception as e:
                        print(f"    获取歌曲失败: {e}")
        
        print("\n播放列表读取完成!")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = read_detailed_playlists()
    if success:
        print("\n播放列表读取成功!")
    else:
        print("\n播放列表读取失败!")










