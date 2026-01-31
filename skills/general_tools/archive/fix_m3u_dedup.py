#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 enhanced_harmonic_set_sorter.py 中的去重逻辑"""

import re

# 读取文件
file_path = 'D:/anti/enhanced_harmonic_set_sorter.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并修复普通 M3U 导出部分
old_m3u_section = '''        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        m3u_file = output_dir / f"{playlist_display_name}_增强调性和谐版_{timestamp}.m3u"
        
        # 生成M3U内容
        m3u_lines = ["#EXTM3U"]
        
        for set_idx, set_tracks in enumerate(sets, 1):
            try:
                print(f"  处理 Set {set_idx}/{len(sets)}...")
            except:
                print(f"  Processing Set {set_idx}/{len(sets)}...")
            
            m3u_lines.append(f"\\n# 分割线 - Set {set_idx} ({len(set_tracks)} 首歌曲)")
            
            for track in set_tracks:
                duration = 0  # M3U不需要精确时长
                m3u_lines.append(f"#EXTINF:{duration},{track['artist']} - {track['title']}")
                m3u_lines.append(track['file_path'])
            
            # 如果不是最后一个set，添加过渡歌曲作为分割标识
            if set_idx < len(sets):
                m3u_lines.append(f"\\n# ========== Set {set_idx + 1} 结束 | Set {set_idx + 2} 开始 ==========")
                # 使用当前set的最后一首歌作为过渡（重复播放），帮助set之间的平滑过渡
                # 这是专业DJ的做法：用一首歌作为两个set之间的桥梁
                last_track = set_tracks[-1]
                
                # 添加过渡标识和重复的最后一首歌
                m3u_lines.append(f"#EXTINF:{duration},{last_track['artist']} - {last_track['title']} [Set过渡 - 重复播放]")
                m3u_lines.append(last_track['file_path'])
                m3u_lines.append("")  # 空行作为分隔
        
        # 写入M3U文件
        try:
            print("  正在写入M3U文件...")
        except:
            print("  Writing M3U file...")
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(m3u_lines))'''

new_m3u_section = '''        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        m3u_file = output_dir / f"{playlist_display_name}_增强调和谐版_{timestamp}.m3u"
        
        # 【V3.0 ULTRA+ 修复】M3U 导出前先去重
        seen_paths = set()
        
        # 生成M3U内容
        m3u_lines = ["#EXTM3U"]
        
        for set_idx, set_tracks in enumerate(sets, 1):
            try:
                print(f"  处理 Set {set_idx}/{len(sets)}...")
            except:
                print(f"  Processing Set {set_idx}/{len(sets)}...")
            
            m3"\\n# 分割线 -u_lines.append(f Set {set_idx} ({len(set_tracks)} 首歌曲)")
            
            for track in set_tracks:
                # 【V3.0 ULTRA+ 修复】跳过已去重的曲目
                path = (track.get('file_path') or '').replace('\\\\', '/').lower()
                if path not in seen_paths:
                    seen_paths.add(path)
                    
                    duration = 0  # M3U不需要精确时长
                    m3u_lines.append(f"#EXTINF:{duration},{track['artist']} - {track['title']}")
                    m3u_lines.append(track['file_path'])
            
            # 如果不是最后一个set，添加过渡歌曲作为分割标识
            if set_idx < len(sets):
                m3u_lines.append(f"\\n# ========== Set {set_idx + 1} 结束 | Set {set_idx + 2} 开始 ==========")
                # 使用当前set的最后一首歌作为过渡（重复播放），帮助set之间的平滑过渡
                # 这是专业DJ的做法：用一首歌作为两个set之间的桥梁
                last_track = set_tracks[-1]
                
                # 添加过渡标识和重复的最后一首歌
                m3u_lines.append(f"#EXTINF:{duration},{last_track['artist']} - {last_track['title']} [Set过渡 - 重复播放]")
                m3u_lines.append(last_track['file_path'])
                m3u_lines.append("")  # 空行作为分隔
        
        # 写入M3U文件
        try:
            print("  正在写入M3U文件...")
        except:
            print("  Writing M3U file...")
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(m3u_lines))'''

if old_m3u_section in content:
    content = content.replace(old_m3u_section, new_m3u_section)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Fixed M3U deduplication in enhanced_harmonic_set_sorter.py')
else:
    print('ERROR: Could not find the M3U export section to fix')



