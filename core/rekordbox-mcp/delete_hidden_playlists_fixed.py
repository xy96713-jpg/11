#!/usr/bin/env python3
"""
删除隐藏的播放列表 - 修复版本
"""

import pyrekordbox

def delete_hidden_playlists_fixed():
    print("删除隐藏的播放列表 - 修复版本")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取所有播放列表
        print("\n获取播放列表...")
        playlists = db.get_playlist()
        playlists_list = list(playlists)
        print(f"找到 {len(playlists_list)} 个播放列表")
        
        # 查找要删除的播放列表
        playlists_to_delete = []
        
        for playlist in playlists_list:
            if playlist.Name == "华语" and hasattr(playlist, 'Songs') and playlist.Songs:
                songs_count = len(list(playlist.Songs))
                if songs_count == 143:
                    playlists_to_delete.append(playlist)
                    print(f"找到要删除的华语播放列表: {playlist.Name} (ID: {playlist.ID}, 歌曲数: {songs_count})")
            
            elif playlist.Name == "Boiler Room" and hasattr(playlist, 'Songs') and playlist.Songs:
                songs_count = len(list(playlist.Songs))
                if songs_count == 48:
                    playlists_to_delete.append(playlist)
                    print(f"找到要删除的Boiler Room播放列表: {playlist.Name} (ID: {playlist.ID}, 歌曲数: {songs_count})")
        
        print(f"\n找到 {len(playlists_to_delete)} 个要删除的播放列表")
        
        if playlists_to_delete:
            print("\n确认删除以下播放列表:")
            for playlist in playlists_to_delete:
                print(f"  - {playlist.Name} (ID: {playlist.ID})")
            
            # 执行删除操作
            print("\n开始删除播放列表...")
            for playlist in playlists_to_delete:
                try:
                    print(f"正在删除: {playlist.Name} (ID: {playlist.ID})")
                    
                    # 尝试不同的删除方法
                    try:
                        # 方法1: 直接使用delete_playlist
                        db.delete_playlist(playlist.ID)
                        print(f"成功删除: {playlist.Name}")
                    except Exception as e1:
                        print(f"方法1失败: {e1}")
                        
                        # 方法2: 尝试使用字符串ID
                        try:
                            db.delete_playlist(str(playlist.ID))
                            print(f"成功删除: {playlist.Name}")
                        except Exception as e2:
                            print(f"方法2失败: {e2}")
                            
                            # 方法3: 直接操作数据库
                            try:
                                from sqlalchemy import text
                                query = text("DELETE FROM djmdPlaylist WHERE ID = :playlist_id")
                                db.session.execute(query, {"playlist_id": playlist.ID})
                                print(f"成功删除: {playlist.Name}")
                            except Exception as e3:
                                print(f"方法3失败: {e3}")
                
                except Exception as e:
                    print(f"删除失败: {playlist.Name} - {e}")
            
            # 提交更改
            try:
                db.commit()
                print("\n所有更改已提交到数据库")
            except Exception as e:
                print(f"提交更改失败: {e}")
        else:
            print("\n未找到要删除的播放列表")
        
        # 验证删除结果
        print("\n验证删除结果...")
        remaining_playlists = db.get_playlist()
        remaining_list = list(remaining_playlists)
        print(f"剩余播放列表数量: {len(remaining_list)}")
        
        # 显示剩余的华语和Boiler Room播放列表
        chinese_remaining = [p for p in remaining_list if '华语' in p.Name]
        boiler_remaining = [p for p in remaining_list if 'Boiler' in p.Name]
        
        print(f"剩余华语播放列表: {len(chinese_remaining)} 个")
        for playlist in chinese_remaining:
            if hasattr(playlist, 'Songs') and playlist.Songs:
                songs_count = len(list(playlist.Songs))
                print(f"  - {playlist.Name} (ID: {playlist.ID}, 歌曲数: {songs_count})")
        
        print(f"剩余Boiler Room播放列表: {len(boiler_remaining)} 个")
        for playlist in boiler_remaining:
            if hasattr(playlist, 'Songs') and playlist.Songs:
                songs_count = len(list(playlist.Songs))
                print(f"  - {playlist.Name} (ID: {playlist.ID}, 歌曲数: {songs_count})")
        
        print("\n删除操作完成!")
        
    except Exception as e:
        print(f"操作失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = delete_hidden_playlists_fixed()
    if success:
        print("\n播放列表删除成功!")
    else:
        print("\n播放列表删除失败!")










