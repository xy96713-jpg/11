#!/usr/bin/env python3
"""
正确读取Rekordbox播放列表
"""

import pyrekordbox

def read_correct_playlists():
    print("正确读取Rekordbox播放列表")
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
                
                # 尝试使用正确的API获取歌曲
                try:
                    # 使用playlist对象的Songs属性
                    if hasattr(playlist, 'Songs') and playlist.Songs:
                        songs_list = list(playlist.Songs)
                        print(f"    歌曲数量: {len(songs_list)}")
                        
                        if songs_list:
                            print("    前3首歌曲:")
                            for j, song in enumerate(songs_list[:3]):
                                print(f"      {j+1}. {song.Title} - {song.ArtistName}")
                                if hasattr(song, 'BPM') and song.BPM:
                                    print(f"         BPM: {song.BPM}")
                                if hasattr(song, 'Key') and song.Key:
                                    print(f"         调性: {song.Key}")
                    else:
                        print("    无歌曲或无法访问歌曲列表")
                        
                except Exception as e:
                    print(f"    获取歌曲失败: {e}")
                
                print()
        
        # 特别关注Boiler Room播放列表
        print("\n重点关注Boiler Room播放列表:")
        print("-" * 40)
        
        boiler_playlists = [p for p in playlists_list if 'Boiler' in p.Name]
        if boiler_playlists:
            for playlist in boiler_playlists:
                print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
                
                try:
                    if hasattr(playlist, 'Songs') and playlist.Songs:
                        songs_list = list(playlist.Songs)
                        print(f"歌曲数量: {len(songs_list)}")
                        
                        if songs_list:
                            print("所有歌曲:")
                            for i, song in enumerate(songs_list):
                                print(f"  {i+1:2d}. {song.Title} - {song.ArtistName}")
                                if hasattr(song, 'BPM') and song.BPM:
                                    print(f"      BPM: {song.BPM}")
                                if hasattr(song, 'Key') and song.Key:
                                    print(f"      调性: {song.Key}")
                                if hasattr(song, 'Length') and song.Length:
                                    print(f"      时长: {song.Length}")
                                print()
                    else:
                        print("无法访问歌曲列表")
                        
                except Exception as e:
                    print(f"获取歌曲失败: {e}")
        
        print("\n播放列表读取完成!")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = read_correct_playlists()
    if success:
        print("\n播放列表读取成功!")
    else:
        print("\n播放列表读取失败!")










