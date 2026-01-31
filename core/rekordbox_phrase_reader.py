#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rekordbox 原生数据读取器
从 Rekordbox 分析文件（.DAT/.EXT）读取歌曲结构、波形等数据

用于标点系统 V6.0 的"Rekordbox 原生数据驱动"架构
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from pyrekordbox.anlz import AnlzFile
    PYREKORDBOX_AVAILABLE = True
except ImportError:
    PYREKORDBOX_AVAILABLE = False
    print("[WARN] pyrekordbox 未安装，段落读取功能不可用")

# Rekordbox Phrase Kind 映射
# 注意：kind=5 和 kind=10 在 Rekordbox 中都可表示结尾段落，但语义略有不同
PHRASE_KINDS = {
    1: 'Intro',
    2: 'Up',
    3: 'Down',
    4: 'Chorus',
    5: 'Outro',
    6: 'Verse',
    7: 'Bridge',
    8: 'Breakdown',
    9: 'Buildup',
    10: 'Fade'  # V7.1 修复：区别于 Outro，表示歌曲尾声渐弱段
}

# Rekordbox 分析文件目录
ANLZ_BASE_DIR = Path(os.environ.get('APPDATA', '')) / 'Pioneer' / 'rekordbox' / 'share' / 'PIONEER' / 'USBANLZ'


class RekordboxPhraseReader:
    """Rekordbox 段落数据读取器"""
    
    def __init__(self, anlz_base: Optional[Path] = None):
        """
        初始化读取器
        
        Args:
            anlz_base: 分析文件根目录，默认为标准 Rekordbox 路径
        """
        self.anlz_base = anlz_base or ANLZ_BASE_DIR
    
    def _get_anlz_path(self, content_uuid: str, extension: str = "EXT") -> Optional[Path]:
        """
        根据 UUID 构建分析文件路径
        
        Args:
            content_uuid: 曲目 UUID（如 'fcb46903-42a0-4b86-8904-41920b7cc6a8'）
            extension: 文件扩展名（DAT/EXT/2EX/3EX）
        
        Returns:
            分析文件路径，不存在则返回 None
        """
        if not content_uuid or len(content_uuid) < 4:
            return None
        
        prefix = content_uuid[:3]
        suffix = content_uuid[3:]
        
        anlz_dir = self.anlz_base / prefix / suffix
        anlz_file = anlz_dir / f"ANLZ0000.{extension}"
        
        if anlz_file.exists():
            return anlz_file
        return None
    
    def get_anchor_time(self, content_uuid: str) -> float:
        """获取歌曲的第一个节拍锚点时间 (PQTZ)"""
        if not PYREKORDBOX_AVAILABLE:
            return 0.0
        
        dat_path = self._get_anlz_path(content_uuid, "DAT")
        if not dat_path:
            return 0.0
            
        try:
            anlz = AnlzFile.parse_file(str(dat_path))
            for tag in anlz.tags:
                if tag.type == "PQTZ" and tag.content.entries:
                    # 返回第一个 entry 的毫秒转换为秒
                    return tag.content.entries[0].time / 1000.0
            return 0.0
        except:
            return 0.0

    def get_phrases(self, content_uuid: str, bpm: float = 128.0) -> List[Dict[str, Any]]:
        """
        获取歌曲的段落列表 (PSSI 数据)
        V7.0 引入 PQTZ 锚点过滤，彻底解决网格偏移。
        """
        if not PYREKORDBOX_AVAILABLE:
            return []
        
        ext_path = self._get_anlz_path(content_uuid, "EXT")
        if not ext_path:
            return []
            
        # 获取物理锚点
        anchor = self.get_anchor_time(content_uuid)
        
        try:
            anlz = AnlzFile.parse_file(str(ext_path))
            phrases = []
            
            for tag in anlz.tags:
                if tag.type == "PSSI":
                    beat_duration = 60.0 / bpm if bpm > 0 else 0.5
                    
                    for entry in tag.content.entries:
                        beat = entry.beat
                        kind = entry.kind
                        kind_name = PHRASE_KINDS.get(kind, f"Unknown({kind})")
                        
                        # 【V7.0 精准公式】
                        # 物理时间 = 锚点 + (Beat - 1) * 拍长
                        # 注意：Rekordbox 的 beat 是从 1 开始计数
                        time_sec = anchor + (beat - 1) * beat_duration
                        
                        # 【V5.3 P1】提取段落强度 (intensity 1-5)
                        intensity = getattr(entry, 'intensity', None)
                        
                        phrases.append({
                            "beat": beat,
                            "time": round(time_sec, 3),
                            "kind": kind_name,
                            "kind_id": kind,
                            "intensity": intensity,  # V5.3 新增
                            "raw_beat": beat # 保留原始 beat 供后续精调
                        })
                    
                    break
            
            return phrases
        
        except Exception as e:
            print(f"[WARN] 读取 PSSI 失败: {e}")
            return []
    
    def get_waveform(self, content_uuid: str) -> List[int]:
        """
        获取波形预览数据（PWAV 数据）
        
        Args:
            content_uuid: 曲目 UUID
        
        Returns:
            波形采样列表（通常 400 个点）
        """
        if not PYREKORDBOX_AVAILABLE:
            return []
        
        dat_path = self._get_anlz_path(content_uuid, "DAT")
        if not dat_path:
            return []
        
        try:
            anlz = AnlzFile.parse_file(str(dat_path))
            
            for tag in anlz.tags:
                if tag.type == "PWAV":
                    return list(tag.content.entries)
            
            return []
        
        except Exception as e:
            print(f"[WARN] 读取 PWAV 失败: {e}")
            return []
    
    def get_beat_grid(self, content_uuid: str) -> List[Dict[str, Any]]:
        """
        获取节拍网格数据（PQTZ 数据）
        
        Args:
            content_uuid: 曲目 UUID
        
        Returns:
            节拍列表，每个包含 beat, time, bpm
        """
        if not PYREKORDBOX_AVAILABLE:
            return []
        
        dat_path = self._get_anlz_path(content_uuid, "DAT")
        if not dat_path:
            return []
        
        try:
            anlz = AnlzFile.parse_file(str(dat_path))
            
            for tag in anlz.tags:
                if tag.type == "PQTZ":
                    beats = []
                    for entry in tag.content.entries:
                        beats.append({
                            "beat": entry.beat,
                            "time": entry.time / 1000.0 if entry.time > 100 else entry.time,
                            "bpm": entry.tempo / 100.0 if entry.tempo else 0
                        })
                    return beats
            
            return []
        
        except Exception as e:
            print(f"[WARN] 读取 PQTZ 失败: {e}")
            return []
    
    def find_phrase(self, phrases: List[Dict], kinds: List[str], position: str = "first") -> Optional[Dict]:
        """
        在段落列表中查找特定类型的段落
        
        Args:
            phrases: 段落列表
            kinds: 要查找的段落类型列表（如 ["Intro", "Up"]）
            position: "first" 或 "last"
        
        Returns:
            找到的段落，未找到则返回 None
        """
        matching = [p for p in phrases if p["kind"] in kinds]
        
        if not matching:
            return None
        
        if position == "first":
            return matching[0]
        elif position == "last":
            return matching[-1]
        
        return matching[0]
    
    def find_phrase_end(self, phrases: List[Dict], kind: str) -> Optional[float]:
        """
        查找某类型段落的结束时间点
        
        Args:
            phrases: 段落列表
            kind: 段落类型（如 "Intro"）
        
        Returns:
            该段落结束时间（即下一个段落的开始时间）
        """
        for i, p in enumerate(phrases):
            if p["kind"] == kind and i < len(phrases) - 1:
                return phrases[i + 1]["time"]
        return None

    def find_phrase_end_by_time(self, phrases: List[Dict], start_time: float) -> Optional[float]:
        """根据开始时间查找段落结束时间"""
        for i, p in enumerate(phrases):
            if abs(p["time"] - start_time) < 0.1 and i < len(phrases) - 1:
                return phrases[i + 1]["time"]
        return None
    
    def calculate_energy_gradient(self, waveform: List[int], duration: float) -> List[Dict]:
        """
        计算波形的能量梯度变化点
        
        Args:
            waveform: 波形采样列表
            duration: 歌曲总时长（秒）
        
        Returns:
            能量变化点列表，按变化幅度排序
        """
        import numpy as np
        
        if not waveform or len(waveform) < 10:
            return []
        
        wf = np.array(waveform)
        gradient = np.gradient(wf)
        time_per_sample = duration / len(waveform)
        
        # 找到梯度变化最大的点
        top_indices = np.argsort(np.abs(gradient))[-10:][::-1]
        
        changes = []
        for idx in top_indices:
            changes.append({
                "time": round(idx * time_per_sample, 2),
                "gradient": round(float(gradient[idx]), 1),
                "amplitude": int(waveform[idx])
            })
        
        return changes


# 便捷函数
def get_rekordbox_phrases(content_uuid: str, bpm: float = 128.0) -> List[Dict]:
    """便捷函数：获取歌曲段落"""
    return RekordboxPhraseReader().get_phrases(content_uuid, bpm)


def get_rekordbox_waveform(content_uuid: str) -> List[int]:
    """便捷函数：获取波形数据"""
    return RekordboxPhraseReader().get_waveform(content_uuid)


if __name__ == "__main__":
    # 测试代码
    test_uuid = "fcb46903-42a0-4b86-8904-41920b7cc6a8"  # hearts2hearts flip
    
    reader = RekordboxPhraseReader()
    
    print("=== 测试 Rekordbox 段落读取器 ===")
    
    phrases = reader.get_phrases(test_uuid, bpm=128.0)
    print(f"\n段落数: {len(phrases)}")
    for p in phrases:
        print(f"  {p['time']:6.2f}s | {p['kind']}")
    
    waveform = reader.get_waveform(test_uuid)
    print(f"\n波形采样点: {len(waveform)}")
    
    if waveform:
        changes = reader.calculate_energy_gradient(waveform, 187)
        print("\n前 5 个能量变化点:")
        for c in changes[:5]:
            print(f"  {c['time']:.2f}s | gradient: {c['gradient']:+.1f}")
