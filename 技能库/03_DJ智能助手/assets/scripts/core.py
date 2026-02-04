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
except ImportError:
    # 回退逻辑
    def get_advanced_harmonic_score(k1, k2): return 70, "Standard"
    def get_smart_pitch_shift(k1, k2): return 0, 0

class MashupIntelligence:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.mashup_threshold = self.config.get("mashup_threshold", 75.0)

    def calculate_mashup_score(self, track1: Dict, track2: Dict, mode: str = 'standard') -> Tuple[float, Dict]:
        """
        [最强大脑推荐标准] 统一 Mashup 评分体系 (V5 Unified)
        融合 11 维度音频特征与 Stems 互补工程逻辑。
        
        mode: 
          - 'standard' / 'set_sorting': 仅开启技术审计，禁用跨界文化逻辑
          - 'mashup_discovery': 开启 V7.1 全火力文化矩阵与反差引擎
        """
        score = 0.0
        details = {}
        
        # 兼容性处理：如果输入是原始对象，尝试提取 analysis 块
        s1 = track1.get('analysis', track1)
        s2 = track2.get('analysis', track2)
        
        # --- 1. BPM & Perceptual Speed (25%) ---
        bpm1 = s1.get('bpm') or 0
        bpm2 = s2.get('bpm') or 0
        
        # 获取感官特征
        od1 = s1.get('onset_density') or 0.5
        od2 = s2.get('onset_density') or 0.5
        busy1 = s1.get('busy_score') or 0.5
        busy2 = s2.get('busy_score') or 0.5
        
        bpm_score = 0.0
        if bpm1 and bpm2:
            # [V7.4] 弹性节奏比对：支持 10% (约 10 BPM) 的创意跨度
            # 仅保留物理意义明确的比率
            ratios = [0.5, 0.75, 1.0, 1.5, 2.0]
            
            # 计算最小偏差比
            diff_list = [abs(bpm1 * r - bpm2) / max(bpm1 * r, bpm2) for r in ratios]
            best_ratio_diff = min(diff_list)
            best_idx = diff_list.index(best_ratio_diff)
            assigned_ratio = ratios[best_idx]
            
            # 分层评分逻辑
            if best_ratio_diff <= 0.05:
                # 💎 黄金区 (0-5%): 高保真匹配
                base_bpm_match = 15.0 * (1.0 - (best_ratio_diff / 0.05))
                details['bpm_tier'] = "Golden"
            elif best_ratio_diff <= 0.10:
                # 🎢 弹性区 (5-10%): 涉及 Master Tempo 变速
                # 基础分降低，且给予 -5 分“弹性惩罚”
                base_bpm_match = 7.0 * (1.0 - (best_ratio_diff - 0.05) / 0.05) - 5.0
                details['bpm_tier'] = "Elastic"
                details['bpm_warning'] = "建议开启 Master Tempo (变速不变调)"
            else:
                base_bpm_match = -50.0 # 严重脱节
            
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
        v1 = s1.get('vocal_ratio') or 0.5
        v2 = s2.get('vocal_ratio') or 0.5
        v_diff = abs(v1 - v2)
        
        if (v1 > 0.6 and v2 < 0.4) or (v2 > 0.6 and v1 < 0.4):
            stems_val = 25
            details['mashup_pattern'] = "A人声 + B伴奏 (极速咬合)"
        else:
            stems_val = max(5, 20 * v_diff)
            details['mashup_pattern'] = "自由 Stem 混搭"
            
        score += stems_val
        details['stems'] = f"{stems_val:.1f}/25"

        # --- 4. 频谱掩蔽与音色 Vibe (20%) ---
        vibe_score = 0.0
        # 4.1 [V7.0] 能量峰值匹配 (Energy Peak Matching)
        en1 = s1.get('energy') or 50
        en2 = s2.get('energy') or 50
        energy_match = 1.0 - abs(en1 - en2) / 100.0
        if energy_match > 0.8: vibe_score += 5.0
        
        # 4.2 音色人格识别 (Spectral Identity)
        tb1 = [s1.get('tonal_balance_low') or 0.5, s1.get('tonal_balance_mid') or 0.3, s1.get('tonal_balance_high') or 0.2]
        tb2 = [s2.get('tonal_balance_low') or 0.5, s2.get('tonal_balance_mid') or 0.3, s2.get('tonal_balance_high') or 0.2]
        tonal_dist = sum((a - b) ** 2 for a, b in zip(tb1, tb2)) ** 0.5
        tonal_sim = max(0, 1.0 - tonal_dist * 2.0)
        vibe_score += tonal_sim * 10
        
        # 4.3 频谱掩蔽 (Spectral Masking Audit)
        b1, b2 = s1.get('spectral_bands', {}), s2.get('spectral_bands', {})
        if b1 and b2:
            # 1. Sub-Bass 对冲审计 (防止能量过载)
            sb1, sb2 = b1.get('sub_bass') or 0.1, b2.get('sub_bass') or 0.1
            if sb1 > 0.6 and sb2 > 0.6:
                vibe_score -= 8.0 # 重度低频冲突惩罚
                details['bass_clash'] = "⚠️ 强力 Sub-Bass 冲突 (建议大幅切除一侧 EQ)"
            elif sb1 > 0.4 and sb2 > 0.4:
                vibe_score -= 3.0 # 中度低频堆叠
            
            # 2. 中频掩蔽审计 (人声/器乐清爽度)
            mid1, mid2 = b1.get('mid_range') or 0.4, b2.get('mid_range') or 0.4
            masking = mid1 * mid2
            # 掩蔽得分映射：范围 0.0-1.0，映射到 0-7 分
            vibe_score += max(-5.0, 7.0 * (1.0 - masking * 2.5))
            
            # 3. 高频平衡
            hi1, hi2 = b1.get('high_presence') or 0.2, b2.get('high_presence') or 0.2
            if abs(hi1 - hi2) < 0.1:
                vibe_score += 2.0 # 同步亮度加分

        score += vibe_score
        details['vibe_balance'] = f"{vibe_score:.1f}/20"

        # --- 5. 律动 DNA 与风格逻辑 (15%) ---
        style_val = 0.0
        dp1, dp2 = s1.get('drum_pattern', ''), s2.get('drum_pattern', '')
        g1, g2 = s1.get('genre', ''), s2.get('genre', '')
        
        if dp1 == dp2 and dp1 != '': style_val += 7
        if g1 == g2 and g1 != '': style_val += 8
        
        # [V5.3 增加：律动深度同步 (Groove Synergy)]
        s_dna1, s_dna2 = s1.get('swing_dna', 0.0), s2.get('swing_dna', 0.0)
        od1, od2 = s1.get('onset_density', 0.0), s2.get('onset_density', 0.0)
        
        groove_bonus = 0.0
        if s_dna1 and s_dna2:
            swing_match = 1.0 - abs(s_dna1 - s_dna2)
            if swing_match > 0.9: groove_bonus += 3.0
            
        if od1 and od2:
            density_match = 1.0 - (abs(od1 - od2) / max(od1, od2))
            if density_match > 0.9: groove_bonus += 3.0
            
        score += (style_val + groove_bonus)
        details['groove_style'] = f"{style_val:.1f}/15"

        # --- 6. [V7.1] 文化矩阵与反差引擎 (Contrast Engine) ---
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

            # 6.2 [V7.1] 黄金人声宇宙 (Golden Cluster)
            # 定义：华语 <-> K-Pop <-> 欧美流行/Hip-Hop 之间的强连接
            keys_mandarin = ['mandarin', 'c-pop', 'chinese', '华语', '中文']
            keys_kpop = ['k-pop', 'kpop', 'korean']
            keys_western = ['pop', 'hip hop', 'rap', 'r&b', 'billboard']

            def has_tag(t_str, keys): return any(k in t_str for k in keys)

            is_c = has_tag(tags1, keys_mandarin) or has_tag(tags2, keys_mandarin)
            is_k = has_tag(tags1, keys_kpop) or has_tag(tags2, keys_kpop)
            is_w = has_tag(tags1, keys_western) or has_tag(tags2, keys_western)

            # 逻辑：至少包含两个不同阵营 (跨界碰撞)
            clusters_present = sum([1 if is_c else 0, 1 if is_k else 0, 1 if is_w else 0])
            if clusters_present >= 2:
                cultural_bonus += 15.0
                details_culture.append("Golden Cluster (跨界人声宇宙)")
            # 或者：单纯的 Hip-Hop x Pop 也在本宇宙内
            elif has_tag(tags1, ['hip hop', 'rap']) and has_tag(tags2, ['pop']) or \
                 has_tag(tags2, ['hip hop', 'rap']) and has_tag(tags1, ['pop']):
                cultural_bonus += 10.0
                details_culture.append("Pop-Rap Synergy")

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
            if details_culture:
                details['cultural_affinity'] = ", ".join(details_culture)

        # [V7.0] 严厉的“换一批”反垄断惩罚
        a1 = track1.get('track_info', {}).get('artist', '')
        a2 = track2.get('track_info', {}).get('artist', '')
        if a1 and a2 and a1 == a2:
            cultural_bonus -= 25.0 
            details['artist_penalty'] = "-25.0 (强制多元化)"
            
        return min(120.0, score + cultural_bonus), details

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
