#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Physical Isolator Module
负责将音频文件从源目录物理隔离（复制）到输出目录，并进行标准化重命名。
"""

import os
import shutil
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

class PhysicalIsolator:
    def __init__(self, output_dir: str = r"D:\生成的set"):
        self.output_dir = Path(output_dir)
        self.map_file = self.output_dir / "processed_tracks_map.json"
        self.mapping = self._load_map()
        
        # Ensure output dir exists
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_map(self) -> Dict:
        if self.map_file.exists():
            try:
                with open(self.map_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_map(self):
        try:
            with open(self.map_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] Failed to save isolation map: {e}")

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件SHA1哈希 (前8位)"""
        try:
            h = hashlib.sha1()
            with open(file_path, 'rb') as f:
                # Read first 1MB for speed
                chunk = f.read(1024 * 1024)
                h.update(chunk)
                # Read file size as well to reduce collision chance on partial hash
                h.update(str(file_path.stat().st_size).encode())
            return h.hexdigest()[:8]
        except Exception:
            return "hash_error"

    def _sanitize_filename(self, name: str) -> str:
        """移除文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

    def process_track(self, file_path: str, metadata: Dict = None) -> str:
        """
        处理单首歌曲：复制并重命名
        
        Args:
            file_path: 源文件路径
            metadata: 元数据 (Title, Artist等)
            
        Returns:
            str: 新文件的绝对路径
        """
        src_path = Path(file_path)
        if not src_path.exists():
            print(f"[Isolator] Source not found: {src_path}")
            return file_path

        # 1. 计算指纹
        file_hash = self._calculate_hash(src_path)
        
        # 2. 检查缓存
        if file_hash in self.mapping:
            cached_path_str = self.mapping[file_hash]['output_path']
            cached_path = Path(cached_path_str)
            if cached_path.exists():
                return str(cached_path)
        
        # 3. 构造新文件名
        # Format: {Hash}_{SafeTitle}.{Ext}
        title = "Unknown"
        if metadata:
            title = metadata.get('title', 'Unknown')
        
        safe_title = self._sanitize_filename(title)
        ext = src_path.suffix
        new_filename = f"{file_hash}_{safe_title}{ext}"
        dest_path = self.output_dir / new_filename
        
        # 4. 执行复制
        try:
            if not dest_path.exists():
                shutil.copy2(src_path, dest_path)
                print(f"[Isolator] Isolated: {src_path.name} -> {new_filename}")
            
            # 5. 更新映射
            self.mapping[file_hash] = {
                'original_path': str(src_path),
                'output_path': str(dest_path),
                'title': title,
                'timestamp': str(os.path.getmtime(dest_path))
            }
            self._save_map()
            
            return str(dest_path)
            
        except Exception as e:
            print(f"[Isolator] Copy failed: {e}")
            return file_path

# 单例模式建议
Isolator = PhysicalIsolator()
