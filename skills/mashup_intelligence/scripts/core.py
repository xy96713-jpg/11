#!/ reentry-v6.4-compatible
# -*- coding: utf-8 -*-
"""
Skill: Mashup Intelligence (V4 Core)
- 11-Dimension Scoring System
- DDJ-800 Pad Action Generator
- Stems Compatibility Engine
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 【Neural Linkage】添加核心库路径支持
# 当前路径为 skills/mashup_intelligence/scripts/core.py，目标指向 d:/anti/core
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "core"))

try:
    from common_utils import get_advanced_harmonic_score, get_smart_pitch_shift
    from audio_dna import map_dna_features
except ImportError:
    # 路径自动补全兜底
    sys.path.insert(0, str(BASE_DIR / "core"))
    from audio_dna import map_dna_features
    from common_utils import get_advanced_harmonic_score, get_smart_pitch_shift
    def map_dna_features(a): return a

class MashupIntelligence:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.mashup_threshold = self.config.get("mashup_threshold", 75.0)

    def calculate_mashup_score(self, track1: Dict, track2: Dict, mode: str = 'standard') -> Tuple[float, Dict]:
        """
        [最强大脑推荐标准 (V19.2 Superbrain Protocol)]
        核心逻辑：实现 100+ 原始音频 DNA 到 11 维专家审计层级的映射与判定。
        
        11 维度框架包括：
        1. BPM Tier (10-BPM Rule) | 2. Key Match (Camelot Distance) | 3. Stems Pattern (Overlay/Alternation)
        4. Vibe Balance | 5. Groove Similarity | 6. Cultural Matrix (DNA/Tags) | 7. Pop Symmetry (Genre Audit)
        8. Anti-Machine Barrier | 9. Perceptual Speed | 10. Energy Alignment | 11. Historical Synergy
        
        硬红线准则：
        - 10-BPM 准则：BPM 偏差 > 12% 直接拦截。
        - 调性铁律：Camelot 距离越过和谐区的 Elite 候选重罚 -20 分。
        - 流派对等：Pop 歌曲严禁配给非标电子或不相关的地下音乐。
        - 数据库真理：严禁推荐未在库内/缓存内检索到的虚构曲目。
        """
        score = 0.0
        details = {}
        
        # [V11.0] 使用全局 DNA 映射逻辑
        s1 = map_dna_features(track1.get('analysis', track1))
        s2 = map_dna_features(track2.get('analysis', track2))
        
        # --- [V16.2 Precision Restoration] 混音师 10-BPM 准则 ---
        bpm1_gate = s1.get('bpm', 0)
        bpm2_gate = s2.get('bpm', 0)
        
        if bpm1_gate > 0 and bpm2_gate > 0:
            # [V16.2] 仅支持 1:1, 0.5x, 2.0x (禁止 1.5x/0.75x)
            ratios = [0.5, 1.0, 2.0]
            best_ratio_diff = min([abs(bpm1_gate * r - bpm2_gate) / max(bpm1_gate * r, bpm2_gate) for r in ratios])
            
            # [V16.2] 硬拦截：偏差超过 12% (约 15 BPM) 直接过滤
            if best_ratio_diff > 0.12:
                return 0.0, {"rejection": f"BPM deviation {best_ratio_diff*100:.1f}% > 12% (Limit exceeded)"}
        
        # 移除了调性硬拦截，允许任何调性通过并进入 11 维度评分受罚
        
        # [V18.0] 同名惩罚 (Same Title Penalty)
        # 混音同首歌（哪怕是不同版本）通常是不专业的，除非是特定 Mashup 需求
        t1_title = track1.get('track_info', {}).get('title', '').lower()
        t2_title = track2.get('track_info', {}).get('title', '').lower()
        if t1_title and t2_title and (t1_title in t2_title or t2_title in t1_title):
            # 这是一个重罚，足以让同名曲目掉出 Elite 梯队
            same_title_penalty = -40.0
        else:
            same_title_penalty = 0.0
        
        # [V14.1/16.1] 同歌拒绝门 (Same Track Only)
        t1_path = track1.get('track_info', {}).get('file_path', track1.get('file_path', ''))
        t2_path = track2.get('track_info', {}).get('file_path', track2.get('file_path', ''))
        if t1_path and t2_path and t1_path == t2_path:
            return 0.0, {"rejection": "Same track"}
        
        # [V15.1/16.0] Stems 模式检测
        v1_gate = s1.get('vocal_ratio', 0.5)
        v2_gate = s2.get('vocal_ratio', 0.5)
        # 仅拒绝极端的“两首都是纯环境音”的情况
        if v1_gate < 0.05 and v2_gate < 0.05:
            return 0.0, {"rejection": "Ambience Only"}
        
        # --- 1. BPM & Perceptual Speed (25%) ---
        bpm1 = s1.get('bpm', 0)
        bpm2 = s2.get('bpm', 0)
        
        # 获取感官特征
        od1 = s1.get('onset_density', 0.5)
        od2 = s2.get('onset_density', 0.5)
        busy1 = s1.get('busy_score', 0.5)
        busy2 = s2.get('busy_score', 0.5)
        
        bpm_score = 0.0
        if bpm1 and bpm2:
            # [V7.5] 弹性节奏比对：支持 15% (约 15-20 BPM) 的创意跨度，适配 Master Tempo 极端拉伸
            # 仅保留物理意义明确的比率
            ratios = [0.5, 0.75, 1.0, 1.5, 2.0]
            
            # 计算最小偏差比
            diff_list = [abs(bpm1 * r - bpm2) / max(bpm1 * r, bpm2) for r in ratios]
            best_ratio_diff = min(diff_list)
            best_idx = diff_list.index(best_ratio_diff)
            assigned_ratio = ratios[best_idx]
            
            # [V16.2] 分层评分 & 10-BPM 惩罚
            if best_ratio_diff <= 0.04:
                # 💎 黄金区 (0-4%, 约 5 BPM): 满分
                base_bpm_match = 15.0
                details['bpm_tier'] = "Golden"
            elif best_ratio_diff <= 0.08:
                # 🏎️ 专业弹性区 (4-8%, 约 10 BPM): 基础分
                base_bpm_match = 5.0
                details['bpm_tier'] = "Professional"
            else:
                # 🎢 创意冒险区 (8-12%, 约 10-15 BPM): 重罚 -10
                # 只有文化/DNA 极其匹配才能挽救
                base_bpm_match = -10.0
                details['bpm_tier'] = "Creative Risk"
                details['bpm_warning'] = f"10-BPM Rule Warning: 偏离 {best_ratio_diff*100:.1f}%"
            
            # [V7.4] 本体感保护：如果不是 1:1 匹配且偏离较大，扣分
            if abs(assigned_ratio - 1.0) > 0.1:
                base_bpm_match -= 5.0
                
            bpm_score += max(0, base_bpm_match)
            
            # 感官速度/繁忙度对齐 (10分)
            perceptual_sim = (1.0 - abs(od1 - od2)) * 5 + (1.0 - abs(busy1 - busy2)) * 5
            bpm_score += perceptual_sim
            
            score += bpm_score
            details['perceptual_speed'] = f"{bpm_score:.1f}/25 ({details.get('bpm_tier', 'Out')})"

        # --- 2. 调性和谐度 (15%) ---
        k1 = s1.get('key', '')
        k2 = s2.get('key', '')
        h_score, h_desc = get_advanced_harmonic_score(k1, k2)
        
        weighted_key = (h_score / 100.0) * 15
        score += weighted_key
        details['key'] = f"{weighted_key:.1f}/15 ({h_desc})"

        # --- 3. Stems 互补强化 (25%) ---
        v1 = s1.get('vocal_ratio', 0.5)
        v2 = s2.get('vocal_ratio', 0.5)
        v_diff = abs(v1 - v2)
        
        if (v1 > 0.6 and v2 < 0.3) or (v2 > 0.6 and v1 < 0.3):
            stems_val = 25
            details['mashup_pattern'] = "Vocal Overlay (A人声 + B伴奏)"
        elif v1 >= 0.45 and v2 >= 0.45:
            # [V18.2] 专业接龙模式 - 拓宽边界，承认 standard pop (0.5) 为潜在接龙
            stems_val = 15.0 
            details['mashup_pattern'] = "Vocal Alternation (乐句接龙/切换)"
            details['mixing_note'] = "⚠️ 建议使用乐句接龙方式混音"
        else:
            stems_val = max(5, 20 * v_diff)
            details['mashup_pattern'] = "Free Stem Mix"
            
        score += stems_val
        details['stems'] = f"{stems_val:.1f}/25"

        # --- 4. 频谱掩蔽与音色 Vibe (20%) ---
        vibe_score = 0.0
        # 4.1 [V7.0] 能量峰值匹配 (Energy Peak Matching)
        en1 = s1.get('energy', 50)
        en2 = s2.get('energy', 50)
        energy_match = 1.0 - abs(en1 - en2) / 100.0
        if energy_match > 0.8: vibe_score += 5.0
        
        # 4.2 音色人格识别 (Spectral Identity)
        tb1 = [s1.get('tonal_balance_low', 0.5), s1.get('tonal_balance_mid', 0.3), s1.get('tonal_balance_high', 0.2)]
        tb2 = [s2.get('tonal_balance_low', 0.5), s2.get('tonal_balance_mid', 0.3), s2.get('tonal_balance_high', 0.2)]
        tonal_dist = sum((a - b) ** 2 for a, b in zip(tb1, tb2)) ** 0.5
        tonal_sim = max(0, 1.0 - tonal_dist * 2.0)
        vibe_score += tonal_sim * 10
        
        # 4.3 频谱掩蔽 (Spectral Masking Audit)
        b1, b2 = s1.get('spectral_bands', {}), s2.get('spectral_bands', {})
        if b1 and b2:
            # 1. Sub-Bass 对冲审计 (防止能量过载)
            sb1, sb2 = b1.get('sub_bass', 0.1), b2.get('sub_bass', 0.1)
            if sb1 > 0.6 and sb2 > 0.6:
                vibe_score -= 8.0 # 重度低频冲突惩罚
                details['bass_clash'] = "⚠️ 强力 Sub-Bass 冲突 (建议大幅切除一侧 EQ)"
            elif sb1 > 0.4 and sb2 > 0.4:
                vibe_score -= 3.0 # 中度低频堆叠
            
            # 2. 中频掩蔽审计 (人声/器乐清爽度)
            mid1, mid2 = b1.get('mid_range', 0.4), b2.get('mid_range', 0.4)
            masking = mid1 * mid2
            # 掩蔽得分映射：范围 0.0-1.0，映射到 0-7 分
            vibe_score += max(-5.0, 7.0 * (1.0 - masking * 2.5))
            
            # 3. 高频平衡
            hi1, hi2 = b1.get('high_presence', 0.2), b2.get('high_presence', 0.2)
            if abs(hi1 - hi2) < 0.1:
                vibe_score += 2.0 # 同步亮度加分

        score += vibe_score
        details['vibe_balance'] = f"{vibe_score:.1f}/20"

        # [V10.0] 律动 DNA 与风格逻辑 (15%)
        style_val = 0.0
        dp1, dp2 = s1.get('drum_pattern', ''), s2.get('drum_pattern', '')
        g1, g2 = s1.get('genre', ''), s2.get('genre', '')
        
        if dp1 == dp2 and dp1 != '': style_val += 7
        if g1 == g2 and g1 != '': style_val += 8
        
        # [V9.0 精准化：律动深度同步 (Groove DNA)]
        s_dna1, s_dna2 = s1.get('swing_dna', 0.0), s2.get('swing_dna', 0.0)
        
        groove_bonus = 0.0
        if s_dna1 and s_dna2:
            swing_match = 1.0 - abs(s_dna1 - s_dna2)
            if swing_match > 0.85: groove_bonus += 5.0
            
        score += (style_val + groove_bonus)
        details['groove_style'] = f"{(style_val + groove_bonus):.1f}/15"

        # --- 6. [V10.0] True-DNA 核心扩展 (Cultural & Performance Sync) ---
        dna_bonus = 0.0
        details_dna = []

        # 6.1 结构化同步 (Structural Alignment)
        pm1 = s1.get('phrase_markers', {}).get('bars_32', [])
        pm2 = s2.get('phrase_markers', {}).get('bars_32', [])
        if pm1 and pm2:
            # 简化逻辑：比较核心 Drop/Chorus 点的乐句跨度
            dna_bonus += 10.0
            details_dna.append("Structure Sync (32-bar matching)")

        # 6.2 情感轨迹对齐 (Emotional Trajectory)
        val1, val2 = s1.get('valence_window_mean', 0.5), s2.get('valence_window_mean', 0.5)
        ar1, ar2 = s1.get('arousal_window_mean', 0.5), s2.get('arousal_window_mean', 0.5)
        emo_dist = ((val1 - val2)**2 + (ar1 - ar2)**2)**0.5
        if emo_dist < 0.15:
            dna_bonus += 15.0
            details_dna.append("Emotional Mirroring (Valence/Arousal)")
        elif emo_dist > 0.6:
            dna_bonus -= 15.0
            details_dna.append("⛔ Mood Clash (情绪背离)")

        # 6.3 风险审计 (Performance Guard)
        conf1 = s1.get('bpm_confidence', 1.0) * s1.get('key_confidence', 1.0)
        conf2 = s2.get('bpm_confidence', 1.0) * s2.get('key_confidence', 1.0)
        stability = s1.get('beat_stability', 1.0) * s2.get('beat_stability', 1.0)
        
        if conf1 * conf2 * stability < 0.4:
            dna_bonus -= 20.0
            details_dna.append("⚠️ High Drift Risk (数据不稳定)")
        elif conf1 * conf2 * stability > 0.8:
            dna_bonus += 5.0
            details_dna.append("Studio-Grade Stability")

        # 6.4 调性转调发现 (Modulation Discovery)
        mods1 = s1.get('key_modulations', [])
        mods2 = s2.get('key_modulations', [])
        target_key = s1.get('key', '')
        if target_key:
            # 检查候选曲目是否在内部转调时经过目标调性
            for m in mods2:
                if m.get('key') == target_key:
                    dna_bonus += 10.0
                    details_dna.append(f"Hidden Match (Modulates to {target_key})")
                    break

        # --- 7. [V7.1] 文化矩阵与反差引擎 (Contrast Engine) ---
        cultural_bonus = 0.0
        details_culture = []
        
        if mode == 'mashup_discovery':
            # 仅在 'mashup_discovery' 模式下激活，避免污染常规 Set 排序
            
            # 准备标签字符串 (Genre + Tags)
            tags1 = (str(s1.get('tags', [])) + " " + str(s1.get('genre', ''))).lower()
            tags2 = (str(s2.get('tags', [])) + " " + str(s2.get('genre', ''))).lower()
            
            # 6.1 [V7.0] 爆破力 (Banger Discovery)
            is_western_banger = any(w in tags1 or w in tags2 for w in ["kanye", "travis", "scott", "hiphop", "trap", "afro", "jersey"])
            if is_western_banger:
                cultural_bonus += 15.0 
                details_culture.append("Banger Discovery")

            # 6.2 [V17.0] 流行阶梯与专业 Remix 对齐 (Pop Symmetry & Remix Synergy)
            # 定义：华语 <-> K-Pop <-> 欧美流行/Hip-Hop 之间的强连接
            keys_mandarin = ['mandarin', 'c-pop', 'chinese', '华语', '中文']
            keys_kpop = ['k-pop', 'kpop', 'korean']
            keys_western = ['pop', 'hip hop', 'rap', 'r&b', 'billboard']
            keys_remix = ['remix', 'edit', 'bootleg', 'rework', 'vip']

            def has_tag(t_str, keys): return any(k in t_str for k in keys)

            is_p1_pop = has_tag(tags1, keys_mandarin + keys_kpop + keys_western)
            is_p2_pop = has_tag(tags2, keys_mandarin + keys_kpop + keys_western)
            is_p1_remix = has_tag(tags1, keys_remix)
            is_p2_remix = has_tag(tags2, keys_remix)

            # [最强大脑] 核心规则：Pop 必须配 Pop 或 Remix
            if is_p1_pop or is_p2_pop:
                # 场景 A: Pop x Pop (跨界宇宙)
                if is_p1_pop and is_p2_pop:
                    is_c = has_tag(tags1, keys_mandarin) or has_tag(tags2, keys_mandarin)
                    is_k = has_tag(tags1, keys_kpop) or has_tag(tags2, keys_kpop)
                    is_w = has_tag(tags1, keys_western) or has_tag(tags2, keys_western)
                    clusters_present = sum([1 if is_c else 0, 1 if is_k else 0, 1 if is_w else 0])
                    
                    if clusters_present >= 2:
                        cultural_bonus += 20.0
                        details_culture.append("Golden Cluster (跨界流行对等)")
                    else:
                        cultural_bonus += 10.0 # 站内同步
                        details_culture.append("Pop Symmetry (同质流行对等)")
                
                # 场景 B: Pop x Remix (专业混音组合)
                elif (is_p1_pop and is_p2_remix) or (is_p2_pop and is_p1_remix):
                    cultural_bonus += 15.0
                    details_culture.append("Pop-Remix Synergy (专业混音对等)")
                
                # 场景 C: Pop x 杂牌 (不专业匹配)
                else:
                    cultural_bonus -= 30.0
                    details_culture.append("⛔ Genre Mismatch (Pop 必须配 Pop 或 Remix)")

            # 6.3 [V7.1] 电子隔离墙 (Anti-Machine Barrier)
            # 拒绝：人声主要曲目 (Vocal Pop) x 纯冷电子 (Techno/Minimal)
            keys_pure_elec = ['techno', 'minimal', 'tech house', 'psytrance', 'trance']
            
            def is_pure_machine(t_str, v_ratio):
                # 只有当人声比例极低 (<0.3) 且包含冷电子标签时
                return has_tag(t_str, keys_pure_elec) and v_ratio < 0.3
                
            def is_vocal_soul(t_str, v_ratio):
                # 人声比例较高 (>0.6) 且属于流行/人声阵营
                return (has_tag(t_str, keys_mandarin) or has_tag(t_str, keys_kpop) or has_tag(t_str, keys_western)) and v_ratio > 0.6

            v1_ratio = s1.get('vocal_ratio', 0.5)
            v2_ratio = s2.get('vocal_ratio', 0.5)

            if (is_vocal_soul(tags1, v1_ratio) and is_pure_machine(tags2, v2_ratio)) or \
               (is_vocal_soul(tags2, v2_ratio) and is_pure_machine(tags1, v1_ratio)):
                cultural_bonus -= 20.0
                details_culture.append("⛔ Anti-Machine (拒绝冷电子)")

            # 6.4 [V7.2] 能量锁位 (Dyna-Vibe) - 解决“快歌配慢歌”的体感冲突
            vibe1 = s1.get('vibe_analysis', {})
            vibe2 = s2.get('vibe_analysis', {})
            
            # 优先使用全局均值 (Window Mean)，它比瞬时 Arousal 更能代表歌曲整体能量
            arousal1 = s1.get('arousal_window_mean', vibe1.get('arousal', 0.5))
            arousal2 = s2.get('arousal_window_mean', vibe2.get('arousal', 0.5))
            
            # Arousal 差距过大惩罚 (能量级不契合)
            arousal_diff = abs(arousal1 - arousal2)
            if arousal_diff > 0.35: # 适度收紧阈值
                cultural_bonus -= 15.0
                details_culture.append("💔 Vibe Dissonance (能量级脱节)")
            elif arousal_diff < 0.12:
                # 能量高度契合加分
                cultural_bonus += 5.0
                
            # 情绪对齐加分 (Synergy)
            mood1 = str(s1.get('vocal_mood', '')).lower()
            mood2 = str(s2.get('vocal_mood', '')).lower()
            aggressive_keywords = ['aggressive', 'energetic', 'vibrant', 'power', 'happy', 'bright']
            
            is_high_energy1 = any(k in mood1 for k in aggressive_keywords) or arousal1 > 0.65
            is_high_energy2 = any(k in mood2 for k in aggressive_keywords) or arousal2 > 0.65
            
            if is_high_energy1 and is_high_energy2:
                cultural_bonus += 10.0
                details_culture.append("🔥 High-Energy Synergy (双高能锁位)")
            elif (is_high_energy1 and arousal2 < 0.45) or (is_high_energy2 and arousal1 < 0.45):
                # 强弱严重失调
                cultural_bonus -= 12.0
                details_culture.append("📉 Energy Mismatch (强弱失调)")

            # 6.5 音色复杂度奖励
            t1, t2 = s1.get('timbre_texture', {}), s2.get('timbre_texture', {})
            if t1.get('complexity', 0) > 0.12 and t2.get('complexity', 0) > 0.12:
                cultural_bonus += 5.0
            
            # 记录文化分详情
            if details_culture or details_dna:
                all_affinity = details_dna + details_culture
                details['cultural_affinity'] = ", ".join(all_affinity)

        # [V16.0] 恢复累加评分体系 (Cumulative Scoring)
        # 确保文化加分能够挽救物理分稍低但极具创意的曲目
        final_total = score + cultural_bonus + dna_bonus + same_title_penalty
        
        # [V18.2 Elite Capping] 最强大脑：只有真正“悦耳”的组合才能突破
        p_pattern = details.get('mashup_pattern', '')
        # 如果调性不匹配 (Key score < 10)，直接降级
        is_harmonic = details.get('key_match', True) # Assume true if not explicitly false
        if h_score < 10.0:
            final_total -= 20.0 # 严厉打击调性冲突的“假匹配”
            details['elite_audit'] = "Capped: Harmonic Dissonance"
            
        is_elite_pattern = "Vocal Overlay" in p_pattern or "Vocal Alternation" in p_pattern
        
        if not is_elite_pattern and final_total > 70.0:
            final_total = 70.0 # 进一步收紧封顶
            details['elite_audit'] = "Capped at 70 (No Professional Stem pattern)"
        
        return min(120.0, final_total), details

    def generate_unified_guide(self, track1: Dict, track2: Dict, score: float, details: Dict) -> List[str]:
        """生成基于统一标准的 Stems / DDJ-800 操作指南。"""
        s1 = track1.get('analysis', track1)
        s2 = track2.get('analysis', track2)
        
        v1 = s1.get('vocal_ratio', 0.5)
        v2 = s2.get('vocal_ratio', 0.5)
        
        guide = []
        guide.append(f"--- [最强大脑 Mashup 执行脚本] (评分: {score:.1f}) ---")
        
        # 角色分配
        if v1 > v2:
            v_title = track1.get('track_info', {}).get('title', 'Deck A')
            i_title = track2.get('track_info', {}).get('title', 'Deck B')
            v_side, i_side = "DECK 1 (主声)", "DECK 2 (底层)"
            shift, _ = get_smart_pitch_shift(s2.get('key',''), s1.get('key',''))
        else:
            v_title = track2.get('track_info', {}).get('title', 'Deck B')
            i_title = track1.get('track_info', {}).get('title', 'Deck A')
            v_side, i_side = "DECK 2 (主声)", "DECK 1 (底层)"
            shift, _ = get_smart_pitch_shift(s1.get('key',''), s2.get('key',''))

        guide.append(f"方案：提取 [{v_title}] 的人声，覆盖至 [{i_title}]。")
        guide.append(f"操作：")
        guide.append(f"  1. [{v_side}] 开启 Vocal Stem，关闭 Drums/Inst Stems。")
        guide.append(f"  2. [{i_side}] 关闭 Vocal Stem，开启 Drums/Inst Stems。")
        
        if shift and shift != 0:
            guide.append(f"  3. 调谐：建议将 {v_side} 移调 {shift:+} 以达到完美谐波。")
            
        guide.append(f"  4. 混音点：建议在 {i_title} 的下次乐句转换处切入。")
        
        return guide

    def get_mashup_sweet_spots(self, track1: Dict, track2: Dict) -> Dict:
        """
        [V4.1 Neural Sync] 识别精确的 Mashup 甜蜜点
        返回：建议的混音时间戳、Stem 动作和理由。
        """
        s1 = track1.get('analysis', track1)
        s2 = track2.get('analysis', track2)
        
        # 提取关键结构点
        intro1 = s1.get('intro_end_time') or s1.get('mix_in_point', 0)
        outro1 = s1.get('outro_start_time') or s1.get('mix_out_point', 0)
        drop1 = s1.get('first_drop_time')
        
        intro2 = s2.get('intro_end_time') or s2.get('mix_in_point', 0)
        outro2 = s2.get('outro_start_time') or s2.get('mix_out_point', 0)
        drop2 = s2.get('first_drop_time')
        
        v1 = s1.get('vocal_ratio', 0.5)
        v2 = s2.get('vocal_ratio', 0.5)
        
        spots = []
        
        # 甜蜜点 1: 主副混搭 (A Vocal + B Instrumental)
        if v1 > 0.7 and v2 < 0.3:
            spots.append({
                "type": "Vocal Overlay",
                "timestamp": intro2,
                "reason": f"[{track1.get('title')}] 强人声与 [{track2.get('title')}] 纯伴奏前奏完美咬合",
                "action": "Open A-Vocal / Open B-Inst"
            })
            
        # 甜蜜点 2: 能量对撞 (Double Drop)
        if drop1 and drop2:
            spots.append({
                "type": "Double Drop",
                "timestamp": drop2,
                "reason": "双轨 Drop 同步，极致能量瞬间",
                "action": "Phase Sync Stems"
            })
            
        return {
            "best_spots": spots,
            "can_mashup": len(spots) > 0
        }

    def get_mashup_archetype(self, track1: Dict, track2: Dict) -> Optional[Dict]:
        """
        [V5.0] 定义混音原型 (Mixing Archetypes)
        根据流派和律动，给出“公式化”的专业转场配方。
        """
        g1 = track1.get('genre', '').lower()
        g2 = track2.get('genre', '').lower()
        
        # 1. House/Techno -> "The Bass Swap"
        if any(w in g1 for w in ['house', 'techno']) and any(w in g2 for w in ['house', 'techno']):
            return {
                "name": "The Bass Swap (低音置换)",
                "steps": [
                    "在 A 轨结束前 16/32 小节开始引入 B 轨。",
                    "切掉 B 轨 Low EQ，将 A/B 音量对齐。",
                    "在乐句转换点 (Drop/Phrase Start)，迅速将 A 轨 Low 切除，同时将 B 轨 Low 推至 0dB。",
                    "保持 8-16 小节双轨叠打，随后缓慢淡出 A 轨 Mid/High。"
                ],
                "rationale": "适用于由 Kick/Bass 驱动的 4/4 拍音乐，确保低频能量平滑切换而无对冲。"
            }
            
        # 2. Pop/Hip-Hop -> "The Vocal Pivot"
        if any(w in g1 for w in ['pop', 'hip hop', 'rap']) and any(w in g2 for w in ['pop', 'hip hop', 'rap']):
            return {
                "name": "The Vocal Pivot (人声轴对称)",
                "steps": [
                    "识别 A 轨人声消失的瞬间（通常是 Outro 开始）。",
                    "在转换点使用 Quick Cut 或 1/2 Beat Echo Out 结束 A 轨。",
                    "直接切入 B 轨带有有力 Hook 或词句的 Intro。",
                    "如果 BPM 差异较大，配合 1/4 Loop 进行同步。"
                ],
                "rationale": "适用于歌词密集型音乐，避免双叠人声导致的信息过载。"
            }
            
        # 3. Future Bass/Trap -> "The Energy Blast"
        if any(w in g1 for w in ['trap', 'future bass', 'dubstep']) and any(w in g2 for w in ['trap', 'future bass', 'dubstep']):
            return {
                "name": "The Energy Blast (能量对撞)",
                "steps": [
                    "开启两轨的 Sync。",
                    "在 A 轨 Build-up 期间悄悄引入 B 轨的氛围层。",
                    "在 A/B 共同的 Drop 点执行 Double Drop。",
                    "利用 Crossfader 快速在两轨的脏低音之间切换以增加动态感。"
                ],
                "rationale": "利用极高的能量密度制造舞台高潮。"
            }
            
        return None
