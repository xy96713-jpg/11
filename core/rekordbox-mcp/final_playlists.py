#!/usr/bin/env python3
"""
最终播放列表读取器 - 使用正确的API
"""

import pyrekordbox

def read_final_playlists():
    print("最终播放列表读取器")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        playlists = db.get_playlist()
        playlists_list = list(playlists)
        print(f"找到 {len(playlists_list)} 个播放列表")
        
        # 重点关注Boiler Room播放列表
        print("\n重点关注Boiler Room播放列表:")
        print("-" * 40)
        boiler_playlists = [p for p in playlists_list if 'Boiler' in p.Name]
        with open("boiler_room_playlist.txt", "w", encoding="utf-8") as f_out:
            if boiler_playlists:
                for playlist in boiler_playlists:
                    print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
                    f_out.write(f'播放列表: {playlist.Name} (ID: {playlist.ID})\n')
                    try:
                        if hasattr(playlist, 'Songs') and playlist.Songs:
                            songs_list = list(playlist.Songs)
                            print(f"歌曲数量: {len(songs_list)}")
                            f_out.write(f'歌曲数量: {len(songs_list)}\n')
                            if songs_list:
                                print("全部歌曲:")
                                f_out.write("编号\t歌名\t艺人\tBPM\t调性\n")
                                for i, song in enumerate(songs_list):
                                    try:
                                        if hasattr(song, 'Content') and song.Content:
                                            content = song.Content
                                            title = getattr(content, 'Title', 'Unknown')
                                            artist = getattr(content, 'ArtistName', 'Unknown')
                                            bpm = getattr(content, 'BPM', 0)
                                            key = getattr(content, 'Key', 'Unknown')
                                            f_out.write(f'{i+1}\t{title}\t{artist}\t{bpm}\t{key}\n')
                                            print(f"  {i+1}. {title} - {artist}\tBPM:{bpm}\t调性:{key}")
                                        else:
                                            print(f"      无法访问Content属性")
                                    except Exception as e:
                                        print(f"      获取歌曲详情失败: {e}")
                            else:
                                print("无歌曲")
                                f_out.write("无歌曲\n")
                        else:
                            print("无法访问歌曲列表")
                            f_out.write("无法访问歌曲列表\n")
                    except Exception as e:
                        print(f"获取歌曲失败: {e}")
                        f_out.write(f"获取歌曲失败: {e}\n")
        
        # 重点关注流行set播放列表
        print("\n重点关注流行set播放列表:")
        print("-" * 40)
        pop_set_playlists = [p for p in playlists_list if 'set' in p.Name and 'Boiler' not in p.Name]
        with open("pop_set_playlist.txt", "w", encoding="utf-8") as f_out_set:
            if pop_set_playlists:
                for playlist in pop_set_playlists:
                    print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
                    f_out_set.write(f'播放列表: {playlist.Name} (ID: {playlist.ID})\n')
                    try:
                        if hasattr(playlist, 'Songs') and playlist.Songs:
                            songs_list = list(playlist.Songs)
                            print(f"歌曲数量: {len(songs_list)}")
                            f_out_set.write(f'歌曲数量: {len(songs_list)}\n')
                            if songs_list:
                                print("全部歌曲:")
                                f_out_set.write("编号\t歌名\t艺人\tBPM\t调性\n")
                                for i, song in enumerate(songs_list):
                                    try:
                                        if hasattr(song, 'Content') and song.Content:
                                            content = song.Content
                                            title = getattr(content, 'Title', 'Unknown')
                                            artist = getattr(content, 'ArtistName', 'Unknown')
                                            bpm = getattr(content, 'BPM', 0)
                                            key = getattr(content, 'Key', 'Unknown')
                                            f_out_set.write(f'{i+1}\t{title}\t{artist}\t{bpm}\t{key}\n')
                                            print(f"  {i+1}. {title} - {artist}\tBPM:{bpm}\t调性:{key}")
                                        else:
                                            print(f"      无法访问Content属性")
                                    except Exception as e:
                                        print(f"      获取歌曲详情失败: {e}")
                            else:
                                print("无歌曲")
                                f_out_set.write("无歌曲\n")
                        else:
                            print("无法访问歌曲列表")
                            f_out_set.write("无法访问歌曲列表\n")
                    except Exception as e:
                        print(f"获取歌曲失败: {e}")
                        f_out_set.write(f"获取歌曲失败: {e}\n")
        
        # 显示所有播放列表的统计信息
        print("\n播放列表统计:")
        print("-" * 30)
        
        for playlist in playlists_list:
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_count = len(list(playlist.Songs))
                    print(f"{playlist.Name}: {songs_count} 首歌曲")
                else:
                    print(f"{playlist.Name}: 无法访问歌曲")
            except:
                print(f"{playlist.Name}: 错误")
        
        print("\n播放列表读取完成!")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = read_final_playlists()
    if success:
        print("\n播放列表读取成功!")
    else:
        print("\n播放列表读取失败!")









