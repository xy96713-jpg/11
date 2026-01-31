#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Brain (V1.0) - 统一大脑适配层
=====================================
目标：统一接口，渐进重构，零风险

职责：
1. 统一所有 Skill 的调用入口
2. 屏蔽底层实现细节
3. 向后兼容现有代码
"""

from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import sys

# 添加 skills 路径
SKILLS_DIR = Path(__file__).parent.parent / "skills"
sys.path.insert(0, str(SKILLS_DIR))

# ============================================================
# 第一层：核心工具 (来自 unified_expert_core)
# ============================================================

class CueStandard:
    """标点标准定义"""
    
    # 色彩常量
    COLOR_BLUE = "0x0000FF"
    COLOR_RED = "0xFF0000"
    COLOR_GREEN = "0x00FF00"
    COLOR_YELLOW = "0xFFFF00"
    COLOR_CYAN = "0x00FFFF"
    COLOR_MAGENTA = "0xFF00FF"
    
    # 标准标签 (A-E 5点系统)
    V5_MAP = {
        'A': {'Name': 'A: [IN] START', 'Color': COLOR_BLUE, 'Num': 0},
        'B': {'Name': 'B: [IN] ENERGY', 'Color': COLOR_YELLOW, 'Num': 1},
        'C': {'Name': 'C: [OUT] START', 'Color': COLOR_BLUE, 'Num': 2},
        'D': {'Name': 'D: [OUT] END', 'Color': COLOR_BLUE, 'Num': 3},
        'E': {'Name': 'E: [DROP] PEAK', 'Color': COLOR_RED, 'Num': 4},
    }
    
    @staticmethod
    def get_cue(char_key: str) -> Dict:
        return CueStandard.V5_MAP.get(char_key, {})


class PhraseQuantizer:
    """乐句量化引擎"""
    
    @staticmethod
    def bars_to_seconds(bars: float, bpm: float) -> float:
        if bpm <= 0: return 0.0
        return bars * 4 * (60.0 / bpm)
    
    @staticmethod
    def quantize(
        timestamp: float, 
        bpm: float, 
        anchor: float = 0.0, 
        dj_rules: Dict = None,
        snap_bars: int = 8
    ) -> float:
        """
        量化时间点到节拍网格
        
        Args:
            timestamp: 原始时间点
            bpm: BPM
            anchor: 锚点
            dj_rules: 配置
            snap_bars: 量化步长 (bars)
        """
        if bpm <= 0: return timestamp
        
        beat_dur = 60.0 / bpm
        beats_from_anchor = (timestamp - anchor) / beat_dur
        quantized_beats = round(beats_from_anchor)
        
        # 乐句对齐
        if snap_bars > 0:
            beats_per_snap = snap_bars * 4
            quantized_beats = round(quantized_beats / beats_per_snap) * beats_per_snap
        
        return max(0.0, anchor + (quantized_beats * beat_dur))


class VocalConflictEngine:
    """人声冲突检测"""

    @staticmethod
    def normalize_region(region) -> Tuple[float, float]:
        if isinstance(region, (list, tuple)):
            return region[0], region[1] if len(region) > 1 else region[0]
        elif isinstance(region, dict):
            return region.get('start', 0.0), region.get('end', 0.0)
        return 0.0, 0.0

    @staticmethod
    def is_active(timestamp: float, regions: List, buffer: float = 0.5) -> bool:
        for r in regions:
            s, e = VocalConflictEngine.normalize_region(r)
            if s - buffer <= timestamp <= e + buffer:
                return True
        return False

    @staticmethod
    def check_conflict(
        track_a: Dict,
        track_b: Dict,
        mix_out: float,
        mix_in: float,
        dj_rules: Dict = None
    ) -> Tuple[float, str]:
        """
        检查人声冲突

        Returns:
            (penalty_score, reason): 惩罚分数和原因
        """
        if not dj_rules:
            dj_rules = {}

        # 获取人声数据
        va = track_a.get('vocals', {}) or {}
        vb = track_b.get('vocals', {}) or {}

        # 如果缺少人声数据，返回无冲突
        if not va or not vb:
            return (0.0, "缺少人声数据")

        # 检查 Mix Out 点是否在 Track A 的人声段
        a_vocal_segments = va.get('segments', []) or []
        a_is_vocal_at_mixout = VocalConflictEngine.is_active(mix_out, a_vocal_segments)

        # 检查 Mix In 点是否在 Track B 的人声段
        b_vocal_segments = vb.get('segments', []) or []
        b_is_vocal_at_mixin = VocalConflictEngine.is_active(mix_in, b_vocal_segments)

        # 检测人声-on-人声冲突
        if a_is_vocal_at_mixout and b_is_vocal_at_mixin:
            penalty = 0.3
            return (penalty, "人声-on-人声冲突")

        # 无冲突
        if a_is_vocal_at_mixout and not b_is_vocal_at_mixin:
            return (0.0, "人声->器乐 (推荐)")
        elif not a_is_vocal_at_mixout and b_is_vocal_at_mixin:
            return (0.0, "器乐->人声 (推荐)")
        else:
            return (0.0, "器乐->器乐 (最佳)")


# ============================================================
# 新增：低音相位冲突检测引擎 (规则 #9)
# ============================================================

class BassPhaseEngine:
    """低音相位冲突检测与 Bass Swap 建议"""

    @staticmethod
    def check_bass_conflict(track_a: Dict, track_b: Dict) -> Dict:
        """
        检测两首曲目之间的低音相位冲突

        Args:
            track_a: 当前曲目（Mix Out）
            track_b: 下一首曲目（Mix In）

        Returns:
            {
                'has_conflict': bool,
                'severity': 'high'/'medium'/'low'/'none',
                'kick_power_a': float,
                'kick_power_b': float,
                'suggestion': str,  # 混音建议
                'eq_params': {  # 推荐 EQ 参数
                    'a_low_cut': int,
                    'b_low_cut': int,
                    'a_high_pass': int,
                    'b_high_pass': int
                }
            }
        """
        # 获取 Kick Drum Power
        a_analysis = track_a.get('analysis', track_a)
        b_analysis = track_b.get('analysis', track_b)

        kick_a = a_analysis.get('kick_drum_power', 0.5)
        kick_b = b_analysis.get('kick_drum_power', 0.5)

        # 判断冲突
        has_conflict = kick_a > 0.7 and kick_b > 0.7

        if not has_conflict:
            # 检查轻度冲突（一方 Kick 较强）
            if kick_a > 0.7 or kick_b > 0.7:
                severity = 'low'
                suggestion = '轻度低频重叠，建议正常 EQ 调整'
                eq = {'a_low_cut': 0, 'b_low_cut': 0, 'a_high_pass': 0, 'b_high_pass': 0}
            else:
                severity = 'none'
                suggestion = '无低频冲突'
                eq = {'a_low_cut': 0, 'b_low_cut': 0, 'a_high_pass': 0, 'b_high_pass': 0}
        else:
            # 严重冲突：双方都有强 Kick
            severity = 'high'
            suggestion = '⚠️ 严重低频冲突！建议使用 Bass Swap 技术'

            # Bass Swap EQ 建议
            if kick_a > kick_b:
                # A 的 Kick 更强，B 做 High Pass
                eq = {
                    'a_low_cut': 0,  # A 保持完整低频
                    'b_low_cut': 200,  # B 在 200Hz 切掉低频
                    'a_high_pass': 0,
                    'b_high_pass': 50  # B 在 50Hz 做 High Pass
                }
            else:
                # B 的 Kick 更强，A 做 High Pass
                eq = {
                    'a_low_cut': 200,  # A 在 200Hz 切掉低频
                    'b_low_cut': 0,  # B 保持完整低频
                    'a_high_pass': 50,
                    'b_high_pass': 0
                }

        return {
            'has_conflict': has_conflict,
            'severity': severity,
            'kick_power_a': kick_a,
            'kick_power_b': kick_b,
            'suggestion': suggestion,
            'eq_params': eq
        }

    @staticmethod
    def generate_mix_advice(track_a: Dict, track_b: Dict, mix_out: float, mix_in: float) -> Dict:
        """
        生成完整的混音透明度建议

        Returns:
            {
                'vocal_clash': {...},
                'bass_conflict': {...},
                'overall_score': float,
                'recommendations': List[str],
                'technique_suggestion': str  # 推荐混音技术
            }
        """
        # 1. 检查人声冲突
        vocal_result = VocalConflictEngine.check_conflict(
            track_a, track_b, mix_out, mix_in, {}
        )

        # 2. 检查低音冲突
        bass_result = BassPhaseEngine.check_bass_conflict(track_a, track_b)

        # 3. 综合评分 (0-100)
        score = 100

        # 人声冲突扣分
        if vocal_result[0] > 0:
            score -= int(vocal_result[0] * 100)

        # 低音冲突扣分
        if bass_result['has_conflict']:
            score -= 30
        elif bass_result['severity'] == 'low':
            score -= 10

        score = max(0, score)

        # 4. 生成建议列表
        recommendations = []

        if vocal_result[0] > 0:
            recommendations.append(f"人声冲突警告: {vocal_result[1]}")
            recommendations.append("建议: 等待 A 曲人声结束后再切入 B 曲")

        if bass_result['has_conflict']:
            eq = bass_result['eq_params']
            recommendations.append(f"低音冲突: Kick A={bass_result['kick_power_a']:.1f}, Kick B={bass_result['kick_power_b']:.1f}")
            recommendations.append(f"Bass Swap EQ: A LowCut@{eq['a_low_cut']}Hz, B HighPass@{eq['b_high_pass']}Hz")

        # 5. 推荐混音技术
        if score >= 90:
            technique = "标准混音 (Standard Blend)"
        elif score >= 70:
            technique = "Filter Sweep 过渡"
        else:
            technique = "需要 Bass Swap + 等待人声结束"

        return {
            'vocal_clash': {
                'has_conflict': vocal_result[0] > 0,
                'reason': vocal_result[1],
                'penalty': vocal_result[0]
            },
            'bass_conflict': bass_result,
            'overall_score': score,
            'recommendations': recommendations,
            'technique_suggestion': technique
        }


# ============================================================
# 第二层：专业审计 (来自 skill_professional_audit)
# ============================================================

class ProfessionalAudit:
    """Set 专业完整度审计"""
    
    @staticmethod
    def calculate_completeness(tracks: List[Dict]) -> Dict:
        """计算 Set 评分"""
        if not tracks or len(tracks) < 2:
            return {"total_score": 0, "breakdown": {}}
        
        # 简化的评分逻辑
        harmonic_scores = []
        bpm_diffs = []
        phrase_aligned = 0
        vocal_clashes = 0
        
        for i in range(len(tracks) - 1):
            curr = tracks[i]
            nxt = tracks[i+1]
            
            # Harmonic
            h_score = curr.get('key_compatibility', 70)
            harmonic_scores.append(h_score)
            
            # BPM
            b_diff = abs(curr.get('bpm', 0) - nxt.get('bpm', 0))
            bpm_diffs.append(b_diff)
            
            # Phrase
            if curr.get('phrase_aligned') or curr.get('pro_hotcues'):
                phrase_aligned += 1
            
            # Vocal
            if nxt.get('vocal_clash_penalty', 0) > 0:
                vocal_clashes += 1
        
        total_transitions = len(tracks) - 1
        
        # 计算各项得分
        s_harmonic = sum(harmonic_scores) / total_transitions / 4 if total_transitions > 0 else 0
        bad_bpm = sum(1 for d in bpm_diffs if d > 8)
        s_bpm = max(0, 25 - (bad_bpm * 5))
        s_phrase = (phrase_aligned / total_transitions * 25) if total_transitions > 0 else 0
        s_vocal = max(0, 25 - (vocal_clashes * 10))
        
        total = s_harmonic + s_bpm + s_phrase + s_vocal
        
        return {
            "total_score": round(total, 1),
            "breakdown": {
                "harmonic_flow": round(s_harmonic, 1),
                "bpm_stability": round(s_bpm, 1),
                "phrase_alignment": round(s_phrase, 1),
                "vocal_safety": round(s_vocal, 1)
            },
            "rating": "Professional" if total > 85 else "Standard" if total > 70 else "Needs Improvement"
        }
    
    @staticmethod
    def get_energy_curve_summary(tracks: List[Dict]) -> str:
        """能量曲线分析"""
        energies = [t.get('energy', 50) for t in tracks]
        if not energies: return "No data"
        
        start_e = sum(energies[:3]) / min(3, len(energies))
        end_e = sum(energies[-3:]) / min(3, len(energies))
        max_e = max(energies)
        max_idx = energies.index(max_e)
        
        if max_idx > len(energies) * 0.6 and end_e < max_e:
            return "Classic Arc (Warm-up -> Peak -> Outro)"
        elif end_e > start_e + 20:
            return "Ascending Tension (Club Style)"
        return "Variable Vibe"


# ============================================================
# 第三层：Mashup 评分 (来自 skill_mashup_intelligence)
# ============================================================

class MashupScorer:
    """Mashup 智能评分"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.mashup_threshold = self.config.get("mashup_threshold", 75.0)
    
    def calculate_score(self, track1: Dict, track2: Dict) -> Tuple[float, Dict]:
        """
        计算 Mashup 兼容性评分 (0-120+)
        
        11 维度评分系统：
        1. BPM 兼容性 (20%)
        2. 调性和谐度 (15%)
        3. Stems 互补 (25%)
        4. 低频保护 (10%)
        5. 风格律动 (15%)
        6. 情感能量 (15%)
        7. 频谱掩蔽 (20%)
        """
        score = 0.0
        details = {}
        
        s1 = track1.get('analysis', track1)
        s2 = track2.get('analysis', track2)
        
        # 1. BPM 兼容性
        bpm1 = s1.get('bpm', 0)
        bpm2 = s2.get('bpm', 0)
        if bpm1 and bpm2:
            diff_ratio = abs(bpm1 - bpm2) / max(bpm1, bpm2)
            if diff_ratio > 0.08:
                return 0.0, {"error": "BPM 跨度超过 8%"}
            bpm_val = max(0, 20 * (1.0 - (diff_ratio / 0.08)))
            score += bpm_val
            details['bpm'] = f"{bpm_val:.1f}/20"
        
        # 2. 调性
        k1, k2 = s1.get('key', ''), s2.get('key', '')
        h_score = self._get_harmonic_score(k1, k2)
        score += (h_score / 100.0) * 15
        details['key'] = f"{(h_score / 100.0) * 15:.1f}/15"
        
        # 3. Stems 互补
        v1, v2 = s1.get('vocal_ratio', 0.5), s2.get('vocal_ratio', 0.5)
        if v1 > 0.7 and v2 < 0.3:
            stems_val = 25
            pattern = "A人声 + B伴奏"
        elif v2 > 0.7 and v1 < 0.3:
            stems_val = 25
            pattern = "B人声 + A伴奏"
        else:
            stems_val = max(5, 20 * abs(v1 - v2))
            pattern = "自由混搭"
        score += stems_val
        details['stems'] = f"{stems_val:.1f}/25 ({pattern})"
        
        # 4. 低频保护
        kp1, kp2 = s1.get('kick_drum_power', 0.5), s2.get('kick_drum_power', 0.5)
        conflict = kp1 + kp2
        bass_score = max(0, 10 * (1.5 - conflict)) if conflict > 0.5 else 10
        score += bass_score
        details['bass'] = f"{bass_score:.1f}/10"
        
        # 5. 风格律动
        dp1, dp2 = s1.get('drum_pattern', ''), s2.get('drum_pattern', '')
        rhythm_score = 7 if dp1 == dp2 else 3.5
        score += rhythm_score + 8  # 假设 genre 匹配
        details['style'] = f"{rhythm_score + 8:.1f}/15"
        
        # 6. 情感能量
        e1, e2 = s1.get('energy', 50)/100.0, s2.get('energy', 50)/100.0
        harmony_score = 15 * (1.0 - abs(e1 - e2))
        score += harmony_score
        details['harmony'] = f"{harmony_score:.1f}/15"
        
        # 7. 频谱掩蔽 (简化版)
        b1, b2 = s1.get('spectral_bands', {}), s2.get('spectral_bands', {})
        if b1 and b2:
            m1, m2 = b1.get('mid_range', 0), b2.get('mid_range', 0)
            collision = m1 * m2 * 10
            masking_val = max(0, 20 * (1.0 - collision))
        else:
            masking_val = 10  # 默认分
        score += masking_val
        details['masking'] = f"{masking_val:.1f}/20"
        
        return score, details
    
    def _get_harmonic_score(self, k1: str, k2: str) -> float:
        """简化和声评分"""
        if not k1 or not k2: return 70.0
        if k1 == k2: return 100.0
        
        # Camelot Wheel 简化逻辑
        compatible = {
            '8A': ['8A', '5A', '9A', '8B', '7A'],
            '9A': ['9A', '6A', '10A', '9B', '8A'],
            '10A': ['10A', '7A', '11A', '10B', '9A'],
        }
        
        for key, matches in compatible.items():
            if k1 == key and k2 in matches:
                return 90.0
        
        # 默认 70 分
        return 70.0
    
    def generate_guide(self, track1: Dict, track2: Dict, score: float) -> List[str]:
        """生成操作指南"""
        s1 = track1.get('analysis', track1)
        s2 = track2.get('analysis', track2)
        
        v1, v2 = s1.get('vocal_ratio', 0.5), s2.get('vocal_ratio', 0.5)
        
        guide = []
        guide.append(f"=== Mashup Guide (评分: {score:.1f}) ===")
        
        if v1 > v2:
            guide.append(f"主声 Deck: {track1.get('title', 'A')}")
            guide.append(f"底层 Deck: {track2.get('title', 'B')}")
            guide.append("操作: Deck1 开启 Vocal Stem，Deck2 开启 Drums/Inst")
        else:
            guide.append(f"主声 Deck: {track2.get('title', 'B')}")
            guide.append(f"底层 Deck: {track1.get('title', 'A')}")
            guide.append("操作: Deck2 开启 Vocal Stem，Deck1 开启 Drums/Inst")
        
        return guide


# ============================================================
# 第四层：Hotcue 生成 (来自 skill_pro_cueing)
# ============================================================

class HotcueGenerator:
    """专业 Hotcue 生成器"""
    
    def __init__(self):
        self.cue_standard = CueStandard()
        self.quantizer = PhraseQuantizer()
        self.vocal_engine = VocalConflictEngine()
    
    def generate_pro_cues(
        self,
        file_path: str,
        bpm: float,
        duration: float,
        structure: Dict = None,
        anchor: float = 0.0,
        vocal_regions: List = None,
        dj_rules: Dict = None,
        custom_mix_points: Dict = None
    ) -> List[Dict]:
        """
        生成专业 Hotcue (A-H 8点系统)
        
        返回格式: [{'kind': 1, 'time': float, 'name': str}, ...]
        kind: 1=A, 2=B, 3=C, 4=D, 5=E, 6=F, 7=G, 8=H
        """
        beat_dur = 60.0 / bpm
        vocal_regions = vocal_regions or []
        dj_rules = dj_rules or {}
        
        # 量化参数
        phrase_bars = dj_rules.get('phrase_bars', 16)
        snap_bars = int(phrase_bars / 2) if phrase_bars >= 16 else 8
        
        # 获取建议点
        custom_points = custom_mix_points or {}
        suggested_in = custom_points.get('mix_in')
        suggested_out = custom_points.get('mix_out')
        
        cues = []
        
        # === A 点 (Mix-In Start) ===
        cue_a = 0.0
        if suggested_in is not None:
            cue_a = self.quantizer.quantize(suggested_in, bpm, anchor, dj_rules, snap_bars=0)
        else:
            cue_a = self.quantizer.quantize(0, bpm, anchor, dj_rules, snap_bars)
        cues.append({'kind': 1, 'time': round(cue_a, 3), 'name': 'A: [IN] START'})
        
        # === B 点 (Verse/Main) ===
        raw_b = suggested_in if suggested_in else structure.get('drop', (0,))[0] if structure else 0
        if raw_b <= 0: raw_b = duration * 0.35
        cue_b = self.quantizer.quantize(raw_b, bpm, anchor, dj_rules, snap_bars if suggested_in is None else 0)
        cues.append({'kind': 2, 'time': round(cue_b, 3), 'name': 'B: [IN] ENERGY'})
        
        # 确保 A < B
        if cue_a >= cue_b: cue_a = max(0, cue_b - 8 * beat_dur)
        
        # === E 点 (Drop/Peak) ===
        raw_e = structure.get('drop', (0,))[0] if structure else 0
        if raw_e <= cue_b: raw_e = cue_b + (32 * beat_dur)
        cue_e = self.quantizer.quantize(raw_e, bpm, anchor, dj_rules)
        if cue_e <= cue_b: cue_e = cue_b + (32 * beat_dur)
        cues.append({'kind': 5, 'time': round(cue_e, 3), 'name': 'E: [DROP] PEAK'})
        
        # === C 点 (Mix-Out Start) ===
        raw_c = suggested_out if suggested_out else structure.get('outro', (0,))[0] if structure else 0
        if raw_c <= cue_e: raw_c = duration * 0.85
        cue_c = self.quantizer.quantize(raw_c, bpm, anchor, dj_rules, snap_bars=8)
        cues.append({'kind': 3, 'time': round(cue_c, 3), 'name': 'C: [OUT] START'})
        
        # === D 点 (End) ===
        cue_d = self.quantizer.quantize(duration, bpm, anchor, dj_rules)
        cues.append({'kind': 4, 'time': round(cue_d, 3), 'name': 'D: [OUT] END'})
        
        return cues
    
    def generate_v5_cues(self, bpm: float, duration: float, mix_in: float = None, mix_out: float = None) -> Dict[str, Dict]:
        """
        生成 A-E 5点系统 (简化版，符合用户需求)
        
        返回: {'A': {'Name': ..., 'Start': ..., 'Num': ..., 'Color': ...}, ...}
        """
        beat_dur = 60.0 / bpm
        bar_8 = 8 * beat_dur
        
        mix_in = mix_in if mix_in is not None else 0
        mix_out = mix_out if mix_out is not None else duration * 0.85
        
        # 量化到网格
        def quantize_to_grid(t, bpm):
            beat_dur = 60.0 / bpm
            beats = round(t / beat_dur)
            return beats * beat_dur
        
        cues = {}
        
        cues['A'] = {
            'Name': 'A: [IN] START',
            'Start': round(quantize_to_grid(mix_in, bpm), 3),
            'Num': 0,
            'Color': self.cue_standard.COLOR_BLUE
        }
        
        cues['B'] = {
            'Name': 'B: [IN] ENERGY',
            'Start': round(quantize_to_grid(mix_in + bar_8, bpm), 3),
            'Num': 1,
            'Color': self.cue_standard.COLOR_YELLOW
        }
        
        cues['C'] = {
            'Name': 'C: [OUT] START',
            'Start': round(quantize_to_grid(mix_out, bpm), 3),
            'Num': 2,
            'Color': self.cue_standard.COLOR_BLUE
        }
        
        cues['D'] = {
            'Name': 'D: [OUT] END',
            'Start': round(quantize_to_grid(duration - bar_8, bpm), 3),
            'Num': 3,
            'Color': self.cue_standard.COLOR_BLUE
        }
        
        cues['E'] = {
            'Name': 'E: [DROP] PEAK',
            'Start': round(quantize_to_grid(duration * 0.35, bpm), 3),
            'Num': 4,
            'Color': self.cue_standard.COLOR_RED
        }
        
        return cues


# ============================================================
# 第五层：能量与 BPM 管理 (来自 skill_phrase_energy, skill_bpm_progressive)
# ============================================================

class EnergyManager:
    """能量曲线管理"""
    
    # 标准能量阶段
    PHASES = {
        "Warm-up": {"min": 30, "max": 55},
        "Build-up": {"min": 50, "max": 70},
        "Peak": {"min": 65, "max": 90},
        "Cool-down": {"min": 40, "max": 75}
    }
    
    @staticmethod
    def validate_curve(tracks: List[Dict]) -> Tuple[bool, List[Dict]]:
        """验证能量曲线"""
        if not tracks:
            return True, []
        
        issues = []
        n = len(tracks)
        
        warm_up_end = n // 5
        build_up_end = 2 * n // 5
        peak_end = 4 * n // 5
        
        phases = [
            ("Warm-up", 0, warm_up_end),
            ("Build-up", warm_up_end, build_up_end),
            ("Peak", build_up_end, peak_end),
            ("Cool-down", peak_end, n)
        ]
        
        for phase_name, start, end in phases:
            config = EnergyManager.PHASES.get(phase_name, {})
            min_e, max_e = config.get("min", 0), config.get("max", 100)
            
            for i in range(start, min(end, n)):
                energy = tracks[i].get('energy', 50)
                if energy < min_e:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "phase": phase_name,
                        "issue": f"能量过低 ({energy} < {min_e})"
                    })
                elif energy > max_e:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "phase": phase_name,
                        "issue": f"能量过高 ({energy} > {max_e})"
                    })
        
        return len([i for i in issues if 'error' in i]) == 0, issues
    
    @staticmethod
    def reorder_for_curve(tracks: List[Dict]) -> List[Dict]:
        """按能量曲线重新排序"""
        if not tracks or len(tracks) < 4:
            return tracks
        
        sorted_tracks = sorted(tracks, key=lambda t: t.get('energy', 50))
        n = len(sorted_tracks)
        
        warm_up = sorted_tracks[:n//5]
        build_up = sorted_tracks[n//5:2*n//5]
        peak = sorted_tracks[3*n//5:]
        cool_down = sorted_tracks[2*n//5:3*n//5]
        
        result = []
        result.extend(sorted(warm_up, key=lambda t: t.get('energy', 50)))
        result.extend(sorted(build_up, key=lambda t: t.get('energy', 50)))
        
        peak_sorted = sorted(peak, key=lambda t: t.get('energy', 50))
        mid = len(peak_sorted) // 2
        result.extend(peak_sorted[:mid])
        result.extend(reversed(peak_sorted[mid:]))
        
        result.extend(sorted(cool_down, key=lambda t: t.get('energy', 50), reverse=True))
        
        return result


class BPMManager:
    """BPM 渐进管理"""
    
    @staticmethod
    def validate_progression(tracks: List[Dict], dj_rules: Dict = None) -> Tuple[bool, List[Dict]]:
        """验证 BPM 渐进"""
        if not tracks or len(tracks) < 2:
            return True, []
        
        dj_rules = dj_rules or {}
        tolerance = dj_rules.get('bpm', {}).get('direct_tolerance', 15.0)
        
        issues = []
        n = len(tracks)
        
        warm_up_end = n // 5
        build_up_end = 2 * n // 5
        peak_end = 4 * n // 5
        
        for i in range(1, n):
            prev_bpm = tracks[i-1].get('bpm', 0)
            curr_bpm = tracks[i].get('bpm', 0)
            
            if not prev_bpm or not curr_bpm:
                continue
            
            diff = curr_bpm - prev_bpm
            
            if i < warm_up_end:
                if diff < -tolerance:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "issue": f"Warm-up 阶段 BPM 异常减速"
                    })
            elif i < build_up_end:
                if diff < -tolerance:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "issue": f"Build-up 阶段 BPM 异常减速"
                    })
            elif i < peak_end:
                if abs(diff) > tolerance:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "issue": f"Peak 阶段 BPM 跳跃过大"
                    })
            else:
                if diff > tolerance:
                    issues.append({
                        "track_idx": i,
                        "title": tracks[i].get('title', 'Unknown'),
                        "issue": f"Cool-down 阶段 BPM 异常加速"
                    })
        
        return True, issues  # 暂时都返回 True，只记录 warning


# ============================================================
# 第六层：导出管理器 (来自 exporters/xml_exporter)
# ============================================================

class ExportManager:
    """统一导出管理器"""
    
    @staticmethod
    def deduplicate_tracks(tracks: List[Dict]) -> List[Dict]:
        """去重 (按 file_path)"""
        seen = set()
        unique = []
        for t in tracks:
            path = (t.get('file_path') or '').replace('\\', '/').lower()
            if path and path not in seen:
                seen.add(path)
                unique.append(t)
        return unique
    
    @staticmethod
    def export_to_m3u(tracks: List[Dict], output_path: Path):
        """导出 M3U 播放列表"""
        ExportManager.deduplicate_tracks(tracks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for t in tracks:
                f.write(f"#EXTINF:{int(t.get('duration', 0))},{t.get('artist', 'Unknown')} - {t.get('title', 'Unknown')}\n")
                f.write(f"{t.get('file_path', '')}\n")
    
    @staticmethod
    def export_to_xml(tracks: List[Dict], output_path: Path, playlist_name: str = "Generated Set"):
        """导出 Rekordbox XML"""
        try:
            from exporters.xml_exporter import export_to_rekordbox_xml
            unique_tracks = ExportManager.deduplicate_tracks(tracks)
            export_to_rekordbox_xml(unique_tracks, output_path, playlist_name)
        except ImportError:
            # 降级：简单 XML 导出
            ExportManager._simple_xml_export(tracks, output_path, playlist_name)
    
    @staticmethod
    def _simple_xml_export(tracks: List[Dict], output_path: Path, playlist_name: str):
        """简单 XML 导出 (降级方案)"""
        import xml.etree.ElementTree as ET
        
        unique_tracks = ExportManager.deduplicate_tracks(tracks)
        
        root = ET.Element("DJ_PLAYLISTS", version="1.0.0")
        ET.SubElement(root, "PRODUCT", Name="rekordbox", Version="6.0.0", Company="Pioneer DJ")
        collection = ET.SubElement(root, "COLLECTION", Entries=str(len(unique_tracks)))
        
        for t in unique_tracks:
            path = t.get('file_path', '').replace('\\', '/')
            ET.SubElement(collection, "TRACK",
                Name=str(t.get('title', 'Unknown')),
                Artist=str(t.get('artist', 'Unknown')),
                Location=f"file://localhost/{path}"
            )
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding='utf-8', xml_declaration=True)


# ============================================================
# 统一大脑入口
# ============================================================

class UnifiedBrain:
    """
    统一大脑 - 单一入口，调用所有功能

    用法:
        brain = UnifiedBrain()

        # 评分
        score, details = brain.mashup_score(track1, track2)

        # 生成 Hotcue
        cues = brain.generate_cues(bpm=126, duration=180)

        # 审计
        audit = brain.audit_set(tracks)

        # 混音透明度检查
        advice = brain.check_mix_transparency(track_a, track_b, mix_out, mix_in)

        # 导出
        brain.export_set(tracks, output_dir)
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # 初始化各模块
        self.mashup_scorer = MashupScorer(self.config)
        self.hotcue_gen = HotcueGenerator()
        self.audit = ProfessionalAudit()
        self.energy = EnergyManager()
        self.bpm = BPMManager()
        self.export_mgr = ExportManager()
    
    # === Mashup 评分 ===
    def mashup_score(self, track1: Dict, track2: Dict) -> Tuple[float, Dict]:
        return self.mashup_scorer.calculate_score(track1, track2)
    
    def mashup_guide(self, track1: Dict, track2: Dict, score: float) -> List[str]:
        return self.mashup_scorer.generate_guide(track1, track2, score)
    
    # === Hotcue 生成 ===
    def generate_cues(
        self,
        bpm: float,
        duration: float,
        mix_in: float = None,
        mix_out: float = None
    ) -> Dict[str, Dict]:
        """生成 A-E 5点 Hotcue"""
        return self.hotcue_gen.generate_v5_cues(bpm, duration, mix_in, mix_out)
    
    def generate_pro_cues(self, **kwargs) -> List[Dict]:
        """生成 A-H 8点专业 Hotcue"""
        return self.hotcue_gen.generate_pro_cues(**kwargs)
    
    # === 专业审计 ===
    def audit_set(self, tracks: List[Dict]) -> Dict:
        return self.audit.calculate_completeness(tracks)
    
    def energy_curve(self, tracks: List[Dict]) -> str:
        return self.audit.get_energy_curve_summary(tracks)
    
    # === 能量与 BPM ===
    def validate_energy(self, tracks: List[Dict]) -> Tuple[bool, List]:
        return self.energy.validate_curve(tracks)
    
    def validate_bpm(self, tracks: List[Dict], dj_rules: Dict = None) -> Tuple[bool, List]:
        return self.bpm.validate_progression(tracks, dj_rules)
    
    def reorder_by_energy(self, tracks: List[Dict]) -> List[Dict]:
        return self.energy.reorder_for_curve(tracks)
    
    # === 导出 ===
    def export_set(
        self,
        tracks: List[Dict],
        output_dir: Path,
        playlist_name: str = "Generated Set"
    ) -> Dict[str, Path]:
        """
        导出完整 Set (TXT + M3U + XML)

        Returns:
            {'m3u': Path, 'xml': Path, 'txt': Path}
        """
        from datetime import datetime
        import os

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()

        result = {}

        # 1. 导出 M3U
        m3u_path = output_dir / f"{clean_name}_{timestamp}.m3u"
        self.export_mgr.export_to_m3u(tracks, m3u_path)
        result['m3u'] = m3u_path

        # 2. 导出 XML
        xml_path = output_dir / f"{clean_name}_{timestamp}.xml"
        self.export_mgr.export_to_xml(tracks, xml_path, playlist_name)
        result['xml'] = xml_path

        # 3. 导出 TXT 报告
        txt_path = output_dir / f"{clean_name}_{timestamp}.txt"
        self._export_report(tracks, txt_path, playlist_name)
        result['txt'] = txt_path

        return result

    # === 混音透明度检查 (规则 #9) ===
    def check_mix_transparency(
        self,
        track_a: Dict,
        track_b: Dict,
        mix_out: float,
        mix_in: float
    ) -> Dict:
        """
        检查混音透明度：人声冲突 + 低音相位抵消

        Returns:
            {
                'vocal_clash': {...},
                'bass_conflict': {...},
                'overall_score': float,
                'recommendations': List[str],
                'technique_suggestion': str
            }
        """
        return BassPhaseEngine.generate_mix_advice(track_a, track_b, mix_out, mix_in)

    def check_bass_conflict(self, track_a: Dict, track_b: Dict) -> Dict:
        """检查低音相位冲突"""
        return BassPhaseEngine.check_bass_conflict(track_a, track_b)

    def insert_bridge_track(self, prev_track: Dict, next_track: Dict, max_gap: float = 15.0) -> Optional[Dict]:
        """
        当 BPM 跨度超过 max_gap 时，自动寻找桥接曲

        Args:
            prev_track: 前一首曲目
            next_track: 下一首曲目
            max_gap: 最大允许的 BPM 跨度

        Returns:
            桥接曲目 dict 或 None
        """
        bpm_gap = abs(prev_track.get('bpm', 0) - next_track.get('bpm', 0))
        if bpm_gap <= max_gap:
            return None

        # 计算理想的桥接 BPM
        prev_bpm = prev_track.get('bpm', 120)
        next_bpm = next_track.get('bpm', 120)
        bridge_bpm = (prev_bpm + next_bpm) / 2

        # 在曲库中寻找合适的桥接曲
        # 这里需要访问曲库，实际实现需要在外部注入曲库
        return {
            'title': f'Bridge Track for {prev_track.get("title", "")} -> {next_track.get("title", "")}',
            'bpm': round(bridge_bpm, 1),
            'reason': f'BPM gap ({bpm_gap:.0f}) exceeds threshold, bridge needed',
            'from_bpm': prev_bpm,
            'to_bpm': next_bpm
        }
    
    def _export_report(self, tracks: List[Dict], output_path: Path, playlist_name: str):
        """生成 TXT 报告"""
        from datetime import datetime
        
        unique = self.export_mgr.deduplicate_tracks(tracks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"Antigravity V3.0 Ultra+ Set Report\n")
            f.write(f"{'='*60}\n\n")
            
            f.write(f"Playlist: {playlist_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tracks: {len(unique)}\n\n")
            
            # 审计
            audit = self.audit_set(unique)
            f.write(f"Set Score: {audit['total_score']}/100 ({audit['rating']})\n")
            f.write(f"Energy Curve: {self.energy_curve(unique)}\n\n")
            
            f.write(f"{'='*60}\n")
            f.write("Track List\n")
            f.write(f"{'='*60}\n\n")
            
            for i, t in enumerate(unique, 1):
                f.write(f"{i}. {t.get('artist', 'Unknown')} - {t.get('title', 'Unknown')}\n")
                f.write(f"   BPM: {t.get('bpm', '?')} | Key: {t.get('key', '?')} | Energy: {t.get('energy', '?')}\n")
                f.write(f"   File: {t.get('file_path', '?')}\n\n")


# 便捷函数
def create_unified_brain(config: Dict = None) -> UnifiedBrain:
    """创建统一大脑实例"""
    return UnifiedBrain(config)

