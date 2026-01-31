#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级标点生成器 V2.3 - [系统大一统版]
===============================================
核心规则：
1. A/B 进入，C/D 退出 (用户习惯统一)
2. 联动 Rekordbox PQTZ (网格) 和 PSSI (段落)
3. 联动人声规避逻辑
4. 接口支持外部混音建议覆盖
"""

import os
import bisect
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from pyrekordbox.anlz import AnlzFile
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def get_rekordbox_analysis(content_id: str) -> Dict:
    """获取全套 RB 分析数据"""
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
                        # Entry (beat, kind)
                        # Kind mapping (approx): 1=Intro, 2=Verse, 3=Chorus/Drop, 4=Chorus/Peak, 6=Bridge, 10=Outro
                        res['phrases'].append({'beat': entry.beat, 'kind': entry.kind})
            except: pass
        return res
    except: return {}

def generate_pro_cues_v2(
    content_id: str,
    duration: float,
    vocal_regions: List[Tuple[float, float]] = None,
    custom_mix_points: Dict = None,
    **kwargs
) -> Dict:
    """
    [系统大一统] 4点标点引擎
    - A: 起始 (Intro Downbeat)
    - B: 进歌完成 (Mix-In End)
    - C: 混音开始 (Mix-Out Start)
    - D: 终点 (Outro End)
    """
    analysis = get_rekordbox_analysis(content_id)
    beat_times = analysis.get('beat_times', [])
    phrases = analysis.get('phrases', [])
    vocal_regions = vocal_regions or []
    
    if not beat_times: return {}
    
    cues = {}
    
    # 辅助工具：判断人声
    def is_vocal(t):
        for s, e in vocal_regions:
            if s - 0.2 <= t <= e + 0.2: return True
        return False

    # 1. A 点: 起始点 / 混音切入点 (Mix-In)
    # 策略：如果 Sorter 有建议，A 点必须 100% 服从大脑建议，因为这是同步的灵魂
    a_idx = 0
    if custom_mix_points and 'mix_in' in custom_mix_points:
        target_t = custom_mix_points['mix_in']
        a_idx = bisect.bisect_left(beat_times, target_t)
        a_name = "A: [MASTER] START"
    else:
        intro_p = next((p for p in phrases if p['kind'] == 1), None)
        if intro_p: a_idx = intro_p['beat'] - 1
        a_name = "A: Start"
    
    cues['A'] = {'Name': a_name, 'Start': beat_times[a_idx], 'Num': 0}

    # 2. B 点: 进歌完成点 (Mix-In End)
    # 策略：B 为辅助参考点，标志着 Intro 结束或人声规避区域
    b_idx = min(a_idx + 64, len(beat_times) - 32) # 默认 16 小节进歌
    # 寻找第二个 Phrase (通常是 Verse 1)
    if len(phrases) >= 2:
        b_idx_p = phrases[1]['beat'] - 1
        if b_idx_p > a_idx: b_idx = b_idx_p
        
    # [大脑优化] 人声规避：B 应该向后推以避开人声
    search_limit = min(b_idx + 64, len(beat_times) - 64)
    while b_idx < search_limit and is_vocal(beat_times[b_idx]):
        b_idx += 4 
            
    cues['B'] = {'Name': 'B: [AI] In-Done', 'Start': beat_times[b_idx], 'Num': 1}

    # 3. C 点: 混音开始点 (Mix-Out Start)
    # 策略：如果 Sorter 有建议，C 点必须 100% 服从，标志着 Set 过渡开始
    c_idx = max(b_idx + 32, len(beat_times) - 65) 
    if custom_mix_points and 'mix_out' in custom_mix_points:
        target_t = custom_mix_points['mix_out']
        c_idx = bisect.bisect_left(beat_times, target_t)
        c_name = "C: [MASTER] END"
    else:
        outro_p = next((p for p in reversed(phrases) if p['kind'] == 10), None)
        if outro_p:
            c_idx = outro_p['beat'] - 1
        c_name = "C: Out-Start"
        
        # 非 Master 模式下的人声规避
        search_limit = b_idx + 32
        while c_idx > search_limit and is_vocal(beat_times[c_idx]):
            c_idx -= 4 

    # 最终防御：确保 A < B < C < D
    if b_idx <= a_idx: b_idx = min(a_idx + 32, len(beat_times)-2)
    if c_idx <= b_idx: c_idx = min(b_idx + 32, len(beat_times)-1)
    
    cues['C'] = {'Name': c_name, 'Start': beat_times[c_idx], 'Num': 2}

    # 4. D 点: 终点 (Outro End)
    d_idx = len(beat_times) - 1
    cues['D'] = {'Name': 'D: End', 'Start': beat_times[d_idx], 'Num': 3}


    # Memory Cues 仅作为关键结构提醒 (非 HotCue)
    memory_cues = []
    
    # 注入混音提示 (Memory Cue at B)
    if custom_mix_points:
        mix_in_t = custom_mix_points.get('mix_in')
        if mix_in_t is not None:
            memory_cues.append({
                'Name': f'AI MIX RECOMMEND: {kwargs.get("mix_type", "Standard")}', 
                'Start': float(mix_in_t), 
                'Num': -1
            })

    # ========== 【V7-PRO】注入 Mashup Intelligence 微观操作指令 ==========
    mi_details = kwargs.get('mi_details', {})
    if mi_details:
        # 1. Stems 互补模式指令
        pattern = mi_details.get('mashup_pattern', '')
        if "A人声 + B伴奏" in pattern:
            # 当前歌曲若是 A (由 Sorter 逻辑决定，此处作为次选曲目通常是 B)
            # 但在 generate_pro_cues_v2 中，我们是为“当前被处理的歌曲”写标点
            # 如果模式是 A人声+B伴奏，且当前歌曲是 B，则建议使用伴奏(Inst)
            memory_cues.append({'Name': '>> MASHUP: USE INST STEM <<', 'Start': beat_times[b_idx], 'Num': -1})
        elif "B人声 + A伴奏" in pattern:
            memory_cues.append({'Name': '>> MASHUP: USE VOCAL STEM <<', 'Start': beat_times[b_idx], 'Num': -1})
            
        # 2. 低频冲突规避
        bass_info = mi_details.get('bass', '')
        if "冲突值:" in bass_info:
            try:
                # 提取冲突值，例如 "5.0/10 (冲突值: 1.50)" -> 1.50
                conflict_val = float(bass_info.split("冲突值:")[1].split(")")[0])
                if conflict_val > 1.3:
                    memory_cues.append({'Name': '!! BASS CLASH: CUT EQ !!', 'Start': beat_times[b_idx], 'Num': -1})
            except: pass


    # 人声碰撞二级预警
    if vocal_regions:
        for s, e in vocal_regions:
            # 仅记录关键人声点
            if s > beat_times[b_idx]:
                memory_cues.append({'Name': '!! VOCAL IN !!', 'Start': max(0, s - 0.5), 'Num': -1})
                break

    return {
        'cues': cues,
        'memory_cues': memory_cues,
        'bpm': analysis.get('bpm', 120.0),
        'anchor': beat_times[0]
    }
