#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查最新文件的去重情况"""

import os
import pathlib
from collections import Counter

def detailed_check(base_dir):
    """详细检查"""
    
    base = pathlib.Path(base_dir)
    print(f'Searching in: {base_dir}')
    print('=' * 70)
    
    # 检查最新的 Boiler Room 文件
    for f in sorted(base.rglob('*200226*')):
        print(f'\n{f.name}')
        print('-' * 50)
        
        try:
            if f.suffix == '.m3u':
                with open(f, 'r', encoding='utf-8') as fp:
                    lines = fp.readlines()
                
                # 提取路径
                paths = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                print(f'  Total paths: {len(paths)}')
                
                # 统计
                path_counts = Counter(paths)
                duplicates = {k: v for k, v in path_counts.items() if v > 1}
                
                if duplicates:
                    print(f'  DUPLICATE PATHS: {len(duplicates)}')
                    for p, c in duplicates.items():
                        print(f'    {os.path.basename(p)}: {c}')
                else:
                    print(f'  No duplicate paths')
                    
                # 提取文件名
                filenames = [os.path.basename(p) for p in paths]
                name_counts = Counter(filenames)
                name_duplicates = {k: v for k, v in name_counts.items() if v > 1}
                
                if name_duplicates:
                    print(f'  DUPLICATE FILENAMES: {len(name_duplicates)}')
                    for n, c in name_duplicates.items():
                        print(f'    {n}: {c}')
                        
        except Exception as e:
            print(f'  Error: {e}')

if __name__ == '__main__':
    detailed_check(r'D:/生成的set')



