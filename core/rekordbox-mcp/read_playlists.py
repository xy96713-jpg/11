#!/usr/bin/env python3
"""
读取Rekordbox播放列表
"""

import pyrekordbox

def read_playlists():
    print("读取Rekordbox播放列表")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        
        # 尝试使用get_playlist方法
        try:
            # 首先获取播放列表ID列表
            playlists = db.get_playlist()
            playlists_list = list(playlists)
            print(f"找到 {len(playlists_list)} 个播放列表")
            
            if playlists_list:
                print("\n播放列表列表:")
                for i, playlist in enumerate(playlists_list[:10]):  # 只显示前10个
                    print(f"{i+1}. {playlist.Name}")
                    print(f"   ID: {playlist.ID}")
                    print(f"   类型: {playlist.Type}")
                    print(f"   歌曲数量: {playlist.SongCount}")
                    print()
                
                # 获取第一个播放列表的详细信息
                if playlists_list:
                    first_playlist = playlists_list[0]
                    print(f"\n详细查看播放列表: {first_playlist.Name}")
                    
                    # 获取播放列表中的歌曲
                    try:
                        songs = db.get_playlist_songs(first_playlist.ID)
                        songs_list = list(songs)
                        print(f"播放列表中有 {len(songs_list)} 首歌曲")
                        
                        if songs_list:
                            print("\n前5首歌曲:")
                            for i, song in enumerate(songs_list[:5]):
                                print(f"  {i+1}. {song.Title} - {song.ArtistName}")
                                print(f"     BPM: {song.BPM}")
                                print(f"     调性: {song.Key}")
                                print(f"     时长: {song.Length}")
                                print()
                    except Exception as e:
                        print(f"获取歌曲列表失败: {e}")
            
        except Exception as e:
            print(f"获取播放列表失败: {e}")
            
            # 尝试直接查询数据库
            try:
                print("\n尝试直接查询数据库...")
                from sqlalchemy import text
                
                # 查询播放列表表
                query = text("SELECT ID, Name, Type, SongCount FROM djmdPlaylist ORDER BY Name")
                result = db.session.execute(query)
                playlists = result.fetchall()
                
                print(f"直接查询找到 {len(playlists)} 个播放列表")
                for playlist in playlists[:10]:
                    print(f"  - {playlist[1]} (ID: {playlist[0]}, 类型: {playlist[2]}, 歌曲数: {playlist[3]})")
                    
            except Exception as e2:
                print(f"直接查询也失败: {e2}")
        
        print("\n播放列表读取完成!")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = read_playlists()
    if success:
        print("\n播放列表读取成功!")
    else:
        print("\n播放列表读取失败!")










