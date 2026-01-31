#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级标点生成器 V3.0 - [审美导航版]
===============================================
核心重构：
1. 命名维度：整合 [Intelligence-V5] 的 Mood, Vibe, Era 标签。
2. 视觉维度：支持色彩编码 (Color Coding) 以区分点位功能。
3. 扩展维度：开放 A-H 全量点位，支持专用的 Mashup 参考点。
4. 精度保障：严格强制吸附 PQTZ 节拍网格。
"""

import os
import bisect
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from pyrekordbox.anlz import AnlzFile
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

# 【Neural Linkage】添加核心库路径支持
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR)) # 添加项目根目录以支持 from core...

# 【色彩定义】
COLORS = {
    'BLUE': "0x0000FF",    # 过渡/结构 (Intro/Outro)
    'RED': "0xFF0000",     # 能量爆发 (Drop/Chorus)
    'GREEN': "0x00FF00",   # 创意/混搭 (Mashup/Bridge)
    'YELLOW': "0xFFFF00",  # 平稳段落 (Verse)
    'CYAN': "0x00FFFF",    # 氛围/填充
    'MAGENTA': "0xFF00FF"  # 特殊点
}

def get_rekordbox_analysis(content_id: str) -> Dict:
    """获取全套 RB 分析数据，支持 PQTZ 和 PSSI"""
    try:
        db = Rekordbox6Database()
        q = text('SELECT BPM, AnalysisDataPath FROM djmdContent WHERE ID = :cid')
        row = db.session.execute(q, {"cid": content_id}).fetchone()
        if not row: return {}
        
        bpm = row[0] / 100.0
        anlz_rel_path = row[1]
        anlz_base = Path(os.environ.get('APPDATA', '')) / 'Pioneer/rekordbox/share'
        dat_path = anlz_base / anlz_rel_path.lstrip('/')
        ext_path = dat_path.with_suffix('.EXT')
        if not ext_path.exists(): ext_path = dat_path.with_suffix('.2EX')
            
        res = {'bpm': bpm, 'beat_times': [], 'phrases': []}
        if dat_path.exists():
            anlz = AnlzFile.parse_file(str(dat_path))
            qtz = anlz.get('PQTZ')
            if qtz and len(qtz) >= 3:
                res['beat_times'] = [float(t) for t in qtz[2]]
        
        if ext_path.exists():
            try:
                anlz_ext = AnlzFile.parse_file(str(ext_path))
                pssi = anlz_ext.get('PSSI')
                if pssi:
                    for entry in pssi.entries:
                        # Kind: 2=Verse, 3=Chorus/Drop, 4=Chorus/Peak, 6=Bridge, 10=Outro
                        res['phrases'].append({'beat': entry.beat, 'kind': entry.kind})
            except: pass
        return res
    except: return {}

def generate_intelligent_cues_v3(
    content_id: str,
    duration: float,
    vocal_regions: List[Tuple[float, float]] = None,
    custom_mix_points: Dict = None,
    track_tags: Dict = None,
    link_data: Dict = None,
    **kwargs
) -> Dict:
    """
    [最强大脑 V5.4.1] 全时域结构感知标点引擎
    """
    analysis = get_rekordbox_analysis(content_id)
    beat_times = analysis.get('beat_times', [])
    phrases = analysis.get('phrases', [])
    vocal_regions = vocal_regions or []
    track_tags = track_tags or {}
    
    if not beat_times: return {}

    # --- 物理结构 Fallback 逻辑 ---
    if not phrases:
        # 如果 Rekordbox 没分析出 Phrase，调用 Librosa 深度扫描
        from core.enhanced_structure_detector import detect_structure_enhanced
        audio_file = kwargs.get('audio_file')
        if audio_file and os.path.exists(audio_file):
            phys_struct = detect_structure_enhanced(audio_file, bpm=analysis.get('bpm'), duration=duration)
            if phys_struct and phys_struct.get('structure'):
                # 转换物理结构为 PSSI 模拟格式
                s = phys_struct['structure']
                if s.get('intro'): phrases.append({'beat': 1, 'kind': 1})
                if s.get('chorus'): 
                    beat_idx = bisect.bisect_left(beat_times, s['chorus'][0])
                    phrases.append({'beat': beat_idx + 1, 'kind': 3}) # 3=Chorus
                if s.get('outro'):
                    beat_idx = bisect.bisect_left(beat_times, s['outro'][0])
                    phrases.append({'beat': beat_idx + 1, 'kind': 10}) # 10=Outro

    cues = {}
    
    def is_vocal(t):
        for r in vocal_regions:
            if isinstance(r, (list, tuple)):
                s, e = r[0], r[1]
            elif isinstance(r, dict):
                s, e = r.get('start', 0), r.get('end', 0)
            else:
                continue
            if s - 0.2 <= t <= e + 0.2: return True
        return False

    # 1. A 点: Mix-In Start
    a_idx = 0
    if custom_mix_points and custom_mix_points.get('mix_in'):
        a_idx = bisect.bisect_left(beat_times, custom_mix_points['mix_in'])
    else:
        intro_p = next((p for p in phrases if p['kind'] == 1), None)
        if intro_p: a_idx = max(0, intro_p['beat'] - 1)
    
    cues['A'] = {'Name': "A: [IN] START", 'Start': beat_times[min(a_idx, len(beat_times)-1)], 'Color': COLORS['BLUE'], 'Num': 0}

    # B 点: Mix-In Done (Verse Start)
    b_idx = min(a_idx + 64, len(beat_times)-1)
    verse_p = next((p for p in phrases if p['kind'] == 2), None)
    if verse_p:
        b_idx_p = verse_p['beat'] - 1
        if a_idx < b_idx_p < a_idx + 128: b_idx = b_idx_p
    
    b_label = "B: [IN] DONE"
    if is_vocal(beat_times[min(b_idx, len(beat_times)-1)]): b_label = "B: !! VOCAL ALERT !!"
    cues['B'] = {'Name': b_label, 'Start': beat_times[min(b_idx, len(beat_times)-1)], 'Color': COLORS['YELLOW'], 'Num': 1}

    # C 点: Mix-Out Start
    c_idx = len(beat_times) - 65
    if custom_mix_points and custom_mix_points.get('mix_out'):
        c_idx = bisect.bisect_left(beat_times, custom_mix_points['mix_out'])
    else:
        outro_p = next((p for p in reversed(phrases) if p['kind'] == 10), None)
        if outro_p and outro_p['beat'] - 1 > b_idx:
            c_idx = outro_p['beat'] - 1
    
    c_idx = max(0, min(c_idx, len(beat_times)-1))
    cues['C'] = {'Name': "C: [OUT] START", 'Start': beat_times[c_idx], 'Color': COLORS['BLUE'], 'Num': 2}

    # D 点: End
    cues['D'] = {'Name': "D: [OUT] END", 'Start': beat_times[-1], 'Color': COLORS['BLUE'], 'Num': 3}

    # 2. 内部能量节点 (E, F, G)
    # E: First Drop / Chorus (红色)
    drop_p = next((p for p in phrases if p['kind'] in [3, 4]), None)
    if drop_p:
        e_idx = max(0, drop_p['beat'] - 1)
        cues['E'] = {'Name': "E: [DROP] PEAK", 'Start': beat_times[min(e_idx, len(beat_times)-1)], 'Color': COLORS['RED'], 'Num': 4}

    # F: Second Drop / Alternative Chorus
    drops = [p for p in phrases if p['kind'] in [3, 4]]
    if len(drops) > 1:
        f_idx = max(0, drops[1]['beat'] - 1)
        cues['F'] = {'Name': "F: [DROP] 2", 'Start': beat_times[min(f_idx, len(beat_times)-1)], 'Color': COLORS['RED'], 'Num': 5}

    # G: Bridge / Breakdown (大桥/间奏 - 青色)
    bridge_p = next((p for p in phrases if p['kind'] == 6), None)
    if bridge_p:
        g_idx = max(0, bridge_p['beat'] - 1)
        cues['G'] = {'Name': "G: [BRIDGE]", 'Start': beat_times[min(g_idx, len(beat_times)-1)], 'Color': COLORS['CYAN'], 'Num': 6}

    # 3. 连通点 (H)
    memory_cues = []
    if link_data:
        next_intro_beats = link_data.get('next_intro_beats', 32)
        h_idx_raw = max(0, len(beat_times) - next_intro_beats - 1)
        # Phrase 对齐：通常吸附在 8 bars (32拍) 或 4 bars (16拍) 上
        snap = 16
        h_idx = (h_idx_raw // snap) * snap
        
        cues['H'] = {
            'Name': f"H: [LINK] -> {link_data.get('next_title', 'NEXT')[:8]}",
            'Start': beat_times[min(h_idx, len(beat_times)-1)],
            'Color': COLORS['GREEN'],
            'Num': 7
        }
        memory_cues.append({
            'Name': f"MIX: 与下一曲 {next_intro_beats} 拍对齐",
            'Start': beat_times[min(h_idx, len(beat_times)-1)],
            'Num': -1
        })

    return {
        'cues': cues,
        'memory_cues': memory_cues,
        'bpm': analysis.get('bpm', 120.0),
        'anchor': beat_times[0] if beat_times else 0.0
    }
