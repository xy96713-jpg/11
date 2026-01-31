#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析所有输出文件的重复歌曲"""

import os
import pathlib
from collections import Counter

def analyze_all_outputs(base_dir):
    """分析目录中所有输出文件的重复歌曲"""
    
    base = pathlib.Path(base_dir)
    print(f'Searching in: {base_dir}')
    print('=' * 70)
    
    files = list(base.rglob('*20260127*'))
    
    for f in sorted(files):
        try:
            if f.suffix == '.m3u':
                # 分析 M3U 文件
                with open(f, 'r', encoding='utf-8') as fp:
                    lines = fp.readlines()
                
                tracks = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tracks.append(line)
                
                counts = Counter(tracks)
                duplicates = {k: v for k, v in counts.items() if v > 1}
                
                print(f'{f.name}:')
                print(f'  Track entries: {len(tracks)}')
                if duplicates:
                    print(f'  DUPLICATES: {len(duplicates)}')
                    for path, count in list(duplicates.items())[:5]:
                        print(f'    - {os.path.basename(path)}: {count} times')
                print()
                
            elif f.suffix == '.csv':
                # 分析 CSV 文件
                with open(f, 'r', encoding='utf-8') as fp:
                    lines = fp.readlines()
                
                tracks = []
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        tracks.append(parts[1])  # Title column
                
                counts = Counter(tracks)
                duplicates = {k: v for k, v in counts.items() if v > 1}
                
                print(f'{f.name}:')
                print(f'  Track rows: {len(tracks)}')
                if duplicates:
                    print(f'  DUPLICATES: {len(duplicates)}')
                    for title, count in list(duplicates.items())[:5]:
                        print(f'    - {title}: {count} times')
                print()
                
        except Exception as e:
            print(f'{f.name}: Error - {e}\n')

if __name__ == '__main__':
    analyze_all_outputs(r'D:/生成的set')



