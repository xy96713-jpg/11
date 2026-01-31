#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: V3-PRO Cache Supplement
- 增量扫描曲库
- 补全缺失的 V3 特征（频谱、律动等）
- 原子化写入缓存
"""

import os
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加导入路径
BASE_DIR = Path(r"d:\anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "skills"))

from enhanced_harmonic_set_sorter import load_cache, save_cache, get_file_hash, deep_analyze_track

def find_all_songs(root_dir):
    """递归查找所有支持的音频文件"""
    exts = ('.mp3', '.wav', '.flac', '.m4a')
    songs = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(exts):
                songs.append(os.path.join(root, f).replace('\\', '/'))
    return songs

def supplement_v3():
    print("🚀 [V3-PRO Supplement] 启动增量分析引擎...")
    
    # 1. 加载当前缓存
    cache = load_cache()
    print(f"📦 当前缓存包含 {len(cache)} 首歌曲。")
    
    # 2. 扫描物理磁盘
    music_roots = [r"D:/song", r"D:/anti/test_songs"] # 根据实际情况调整
    all_disk_songs = []
    for root in music_roots:
        if os.path.exists(root):
            print(f"📂 正在扫描目录: {root}...")
            all_disk_songs.extend(find_all_songs(root))
            
    print(f"🔍 磁盘共发现 {len(all_disk_songs)} 首音频文件。")
    
    # 3. 识别待处理任务
    tasks = []
    for fp in all_disk_songs:
        f_hash = get_file_hash(fp)
        if not f_hash: continue
        
        needs_analysis = False
        existing_entry = cache.get(f_hash)
        
        if not existing_entry:
            needs_analysis = True
            print(f"🆕 发现新歌: {os.path.basename(fp)}")
        else:
            analysis = existing_entry.get('analysis', {})
            # 检查是否缺失 V3 核心维度
            if "spectral_bands" not in analysis or "swing_dna" not in analysis:
                needs_analysis = True
                print(f"🆙 需要补齐 V3 维度: {os.path.basename(fp)}")
        
        if needs_analysis:
            tasks.append((fp, f_hash))
            
    if not tasks:
        print("✅ 所有歌曲均已具备 V3-PRO 特征，无需处理。")
        return

    print(f"🛠️  共有 {len(tasks)} 项任务待处理。开始批量深度分析...")
    
    # 4. 批量处理 (使用限制核心数的并发，避免爆内存)
    count = 0
    total = len(tasks)
    
    # 为了演示，我们先处理一部分核心曲目，或者分批保存
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 显式传入 existing_analysis 以触发增量补全模式 (BPM/Key 不重做)
        future_to_song = {
            executor.submit(deep_analyze_track, fp, existing_analysis=cache.get(h, {}).get('analysis')): (fp, h) 
            for fp, h in tasks
        }
        
        for future in as_completed(future_to_song):
            fp, h = future_to_song[future]
            count += 1
            try:
                res = future.result()
                if res:
                    # 获取旧有的分析结果，保留可能存在的手动标记
                    old_analysis = cache.get(h, {}).get('analysis', {})
                    if old_analysis:
                        # 合并，新维度覆盖旧维度，但保留旧有的 rekordbox_cues 等
                        for k, v in old_analysis.items():
                            if k not in res:
                                res[k] = v
                                
                    # 更新缓存条目
                    stat = os.stat(fp)
                    cache[h] = {
                        'cache_key': h,
                        'file_path': fp,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size,
                        'analysis': res,
                        'updated_at': time.strftime("%Y-%m-%dT%H:%M:%S"),
                        'analyzer_version': 'v1.2-v3pro'
                    }
                    print(f"✅ [{count}/{total}] 已完成: {os.path.basename(fp)}")
                else:
                    print(f"❌ [{count}/{total}] 分析失败: {os.path.basename(fp)}")
            except Exception as e:
                print(f"⚠️ [{count}/{total}] 发生错误: {e}")
            
            # 每 10 首保存一次，防止中途崩溃丢失进度
            if count % 10 == 0:
                save_cache(cache)
                print(f"💾 进度已自动保存 (已处理 {count} 首)")

    # 5. 最终保存
    save_cache(cache)
    print(f"🏁 任务完成！当前缓存已更新为 V3-PRO 标准。")

if __name__ == "__main__":
    supplement_v3()
