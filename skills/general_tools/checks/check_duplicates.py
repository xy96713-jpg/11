#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 XML 文件中的重复歌曲"""

import os
import pathlib
from collections import Counter

def analyze_xml_duplicates(base_dir):
    """分析目录中 XML 文件的重复歌曲"""
    
    base = pathlib.Path(base_dir)
    print(f'Searching in: {base_dir}')
    print('=' * 60)
    
    for f in base.rglob('*.xml'):
        if '20260127' in f.name and 'Master' not in f.name:
            try:
                content = f.read_text(encoding='utf-8')
                # 统计 TRACK 元素
                tracks = content.count('<TRACK ')
                print(f'{f.name}:')
                print(f'  TRACK count: {tracks}')
                
                # 提取所有 Track 名称
                track_names = []
                lines = content.split('\n')
                for line in lines:
                    if '<TRACK ' in line and 'Name=' in line:
                        # 提取 Name 属性
                        start = line.find('Name="') + 7
                        end = line.find('"', start)
                        if start > 6:
                            name = line[start:end]
                            track_names.append(name)
                
                if track_names:
                    counts = Counter(track_names)
                    duplicates = {k: v for k, v in counts.items() if v > 1}
                    if duplicates:
                        print(f'  DUPLICATES:')
                        for name, count in sorted(duplicates.items(), key=lambda x: -x[1])[:10]:
                            print(f'    - \"{name}\": {count} times')
                    else:
                        print(f'  No duplicates')
                print()
            except Exception as e:
                print(f'{f.name}: Error - {e}\n')

if __name__ == '__main__':
    analyze_xml_duplicates(r'D:/生成的set')



