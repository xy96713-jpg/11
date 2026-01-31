#!/usr/bin/env python3
"""
诚实的华语歌曲分析 - 只显示真实存在的数据
"""

import pyrekordbox

def honest_chinese_analysis():
    print("诚实的华语歌曲分析")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        print("成功连接到Rekordbox数据库")
        
        # 获取华语播放列表
        print("\n获取华语播放列表...")
        playlists = db.get_playlist()
        playlists_list = list(playlists)
        
        chinese_playlists = [p for p in playlists_list if '华语' in p.Name]
        print(f"找到 {len(chinese_playlists)} 个华语播放列表")
        
        if not chinese_playlists:
            print("未找到华语播放列表")
            return False
        
        # 分析华语播放列表
        for playlist in chinese_playlists:
            print(f"\n播放列表: {playlist.Name} (ID: {playlist.ID})")
            
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_list = list(playlist.Songs)
                    print(f"歌曲数量: {len(songs_list)}")
                    
                    # 只显示实际存在的歌曲
                    real_songs = []
                    for i, song in enumerate(songs_list):
                        try:
                            if hasattr(song, 'Content') and song.Content:
                                content = song.Content
                                
                                # 提取真实存在的歌曲信息
                                title = getattr(content, 'Title', None)
                                artist = getattr(content, 'ArtistName', None)
                                bpm = getattr(content, 'BPM', None)
                                
                                if title and title != 'Unknown':
                                    song_info = {
                                        'title': title,
                                        'artist': artist if artist and artist != 'Unknown' else 'Unknown',
                                        'bpm': bpm / 100.0 if bpm and bpm > 100 else bpm if bpm else None
                                    }
                                    real_songs.append(song_info)
                                    
                        except Exception as e:
                            print(f"  歌曲 {i+1} 处理失败: {e}")
                            continue
                    
                    print(f"成功提取 {len(real_songs)} 首真实歌曲")
                    
                    if real_songs:
                        print(f"\n真实歌曲列表 (前20首):")
                        for i, song in enumerate(real_songs[:20]):
                            print(f"  {i+1:2d}. {song['title']} - {song['artist']}")
                            if song.get('bpm'):
                                print(f"      BPM: {song['bpm']:.1f}")
                            print()
                        
                        # 只分析真实存在的BPM数据
                        real_bpms = [s['bpm'] for s in real_songs if s.get('bpm') and s['bpm'] > 0]
                        if real_bpms:
                            print(f"\nBPM分析 (基于 {len(real_bpms)} 首有BPM数据的歌曲):")
                            print(f"  平均BPM: {sum(real_bpms) / len(real_bpms):.1f}")
                            print(f"  最低BPM: {min(real_bpms):.1f}")
                            print(f"  最高BPM: {max(real_bpms):.1f}")
                        
                        # 只分析真实存在的艺术家
                        real_artists = [s['artist'] for s in real_songs if s.get('artist') and s['artist'] != 'Unknown']
                        if real_artists:
                            artist_counts = {}
                            for artist in real_artists:
                                artist_counts[artist] = artist_counts.get(artist, 0) + 1
                            
                            sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
                            print(f"\n艺术家统计 (基于真实数据):")
                            for artist, count in sorted_artists[:10]:
                                print(f"  {artist}: {count} 首")
                    else:
                        print("未找到可显示的真实歌曲")
                        
                else:
                    print("无法访问歌曲列表")
                    
            except Exception as e:
                print(f"分析播放列表失败: {e}")
        
        print("\n分析完成 - 只显示真实存在的数据")
        
    except Exception as e:
        print(f"分析失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = honest_chinese_analysis()
    if success:
        print("\n华语歌曲分析成功!")
    else:
        print("\n华语歌曲分析失败!")










