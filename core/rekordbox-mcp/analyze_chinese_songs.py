#!/usr/bin/env python3
"""
分析华语播放列表中的歌曲
"""

import pyrekordbox

def analyze_chinese_songs():
    print("分析华语播放列表中的歌曲")
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
        
        # 分析每个华语播放列表
        all_chinese_songs = []
        
        for playlist in chinese_playlists:
            print(f"\n分析播放列表: {playlist.Name} (ID: {playlist.ID})")
            
            try:
                if hasattr(playlist, 'Songs') and playlist.Songs:
                    songs_list = list(playlist.Songs)
                    print(f"歌曲数量: {len(songs_list)}")
                    
                    # 分析每首歌曲
                    for i, song in enumerate(songs_list):
                        try:
                            if hasattr(song, 'Content') and song.Content:
                                content = song.Content
                                
                                # 提取歌曲信息
                                song_info = {
                                    'title': getattr(content, 'Title', 'Unknown'),
                                    'artist': getattr(content, 'ArtistName', 'Unknown'),
                                    'bpm': getattr(content, 'BPM', 0),
                                    'key': getattr(content, 'Key', None),
                                    'length': getattr(content, 'Length', 0),
                                    'rating': getattr(content, 'Rating', 0),
                                    'play_count': getattr(content, 'DJPlayCount', 0),
                                    'year': getattr(content, 'ReleaseYear', None),
                                    'genre': getattr(content, 'Genre', None)
                                }
                                
                                # 处理BPM（除以100）
                                if song_info['bpm'] and song_info['bpm'] > 100:
                                    song_info['bpm'] = song_info['bpm'] / 100.0
                                
                                # 处理调性
                                if song_info['key'] and hasattr(song_info['key'], 'Name'):
                                    song_info['key_name'] = song_info['key'].Name
                                else:
                                    song_info['key_name'] = 'Unknown'
                                
                                # 处理时长（转换为秒）
                                if song_info['length']:
                                    song_info['duration_seconds'] = song_info['length'] / 1000.0
                                else:
                                    song_info['duration_seconds'] = 0
                                
                                all_chinese_songs.append(song_info)
                                
                        except Exception as e:
                            print(f"  歌曲 {i+1} 分析失败: {e}")
                            continue
                    
                    print(f"成功分析 {len([s for s in all_chinese_songs if s.get('title') != 'Unknown'])} 首歌曲")
                else:
                    print("无法访问歌曲列表")
                    
            except Exception as e:
                print(f"分析播放列表失败: {e}")
        
        if all_chinese_songs:
            print(f"\n华语歌曲分析结果:")
            print("=" * 50)
            
            # 基本统计
            valid_songs = [s for s in all_chinese_songs if s.get('title') != 'Unknown']
            print(f"总歌曲数: {len(valid_songs)}")
            
            # BPM分析
            bpm_values = [s['bpm'] for s in valid_songs if s.get('bpm') and s['bpm'] > 0]
            if bpm_values:
                print(f"\nBPM分析:")
                print(f"  平均BPM: {sum(bpm_values) / len(bpm_values):.1f}")
                print(f"  最低BPM: {min(bpm_values):.1f}")
                print(f"  最高BPM: {max(bpm_values):.1f}")
                
                # BPM分布
                bpm_ranges = {
                    '慢歌 (60-90)': len([b for b in bpm_values if 60 <= b <= 90]),
                    '中慢 (90-120)': len([b for b in bpm_values if 90 < b <= 120]),
                    '中快 (120-140)': len([b for b in bpm_values if 120 < b <= 140]),
                    '快歌 (140+)': len([b for b in bpm_values if b > 140])
                }
                print(f"  BPM分布:")
                for range_name, count in bpm_ranges.items():
                    print(f"    {range_name}: {count} 首")
            
            # 调性分析
            key_values = [s['key_name'] for s in valid_songs if s.get('key_name') and s['key_name'] != 'Unknown']
            if key_values:
                print(f"\n调性分析:")
                key_counts = {}
                for key in key_values:
                    key_counts[key] = key_counts.get(key, 0) + 1
                
                # 显示最常见的调性
                sorted_keys = sorted(key_counts.items(), key=lambda x: x[1], reverse=True)
                print(f"  最常见调性:")
                for key, count in sorted_keys[:10]:
                    print(f"    {key}: {count} 首")
            
            # 艺术家分析
            artists = [s['artist'] for s in valid_songs if s.get('artist') and s['artist'] != 'Unknown']
            if artists:
                print(f"\n艺术家分析:")
                artist_counts = {}
                for artist in artists:
                    artist_counts[artist] = artist_counts.get(artist, 0) + 1
                
                # 显示最常见的艺术家
                sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
                print(f"  最常见艺术家:")
                for artist, count in sorted_artists[:10]:
                    print(f"    {artist}: {count} 首")
            
            # 显示一些歌曲示例
            print(f"\n歌曲示例 (前10首):")
            for i, song in enumerate(valid_songs[:10]):
                print(f"  {i+1:2d}. {song['title']} - {song['artist']}")
                if song.get('bpm'):
                    print(f"      BPM: {song['bpm']:.1f}")
                if song.get('key_name') and song['key_name'] != 'Unknown':
                    print(f"      调性: {song['key_name']}")
                if song.get('duration_seconds'):
                    minutes = int(song['duration_seconds'] // 60)
                    seconds = int(song['duration_seconds'] % 60)
                    print(f"      时长: {minutes}:{seconds:02d}")
                print()
            
            # 推荐混音组合
            print(f"\n推荐混音组合:")
            print("-" * 30)
            
            # 按BPM分组
            bpm_groups = {}
            for song in valid_songs:
                if song.get('bpm') and song['bpm'] > 0:
                    bpm = round(song['bpm'])
                    if bpm not in bpm_groups:
                        bpm_groups[bpm] = []
                    bpm_groups[bpm].append(song)
            
            # 找到相近BPM的歌曲
            similar_bpm_songs = []
            for bpm, songs in bpm_groups.items():
                if len(songs) >= 2:
                    similar_bpm_songs.append((bpm, songs))
            
            if similar_bpm_songs:
                print("相近BPM的歌曲组合:")
                for bpm, songs in sorted(similar_bpm_songs)[:5]:
                    print(f"  BPM {bpm}:")
                    for song in songs[:3]:  # 显示前3首
                        print(f"    - {song['title']} - {song['artist']}")
                    print()
            
        else:
            print("未找到可分析的华语歌曲")
        
        print("\n华语歌曲分析完成!")
        
    except Exception as e:
        print(f"分析失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = analyze_chinese_songs()
    if success:
        print("\n华语歌曲分析成功!")
    else:
        print("\n华语歌曲分析失败!")










