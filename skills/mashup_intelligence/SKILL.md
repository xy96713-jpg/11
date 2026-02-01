---
name: mashup_intelligence
description: 音乐混音智能匹配引擎 (V7.0)。涵盖 BPM 比例弹性匹配、文化 DNA 共鸣、音频频谱特征检测及全方位混音评分算法。
triggers: ["寻找混音搭档", "mashup", "匹配度分析", "banger discovery"]
---

# Mashup Intelligence (混音智核)

## 0. 核心能力
本技能提供专家级的歌曲匹配评分，支持跨曲风、跨速度的深度律动分析。其核心算法基于 11 个音频维度进行加权计算。

## 1. 算法特征 (Algorithm Hooks)
- **BPM 动态门控**：严格遵循“10-BPM 准则”。偏差 >12% 硬拦截；8%-12% 阶梯惩罚。
- **调性和谐铁律**：基于 Camelot Wheel（五度圈）计算。不满足相邻调性者扣除 20 分并封锁 Elite 资格。
- **Pop 对称性 (Pop Symmetry)**：流行歌曲必须配流行或专业 Remix。Pop x 非标电子重罚 -30 分。
- **Stems 互补强化**：识别 Vocal Overlay 与 Vocal Alternation。非 Elite Pattern 分值封顶 70 分。

## 2. 11 维度专家审计 (11-Dimension Framework)
系统将 100+ 项底层音频 DNA 特征映射为 11 个专业维度，包括：
`Harmonic Synergy`, `Vocal Balance`, `Arousal Alignment`, `Cultural Matrix`, `Anti-Machine Barrier`, `Groove Precision` 等。

## 3. 标准操作规程 (SOP - 最强大脑)
1. **全库审计**：强制执行 `GLOBAL SCAN` 对比数据库中真实存在的歌曲。
2. **黄金三强 (Top 3 Only)**：不向用户提供海量模糊选项，仅输出分值最高的前 3 个黄金组合。
3. **证据化报告**：报告必须包含物理数据比对表与 11 维度审计明细。

## 5. 安全红线 (Safety Guardrails) [CRITICAL]
- **数据库真实性 (Database Truth)**：严禁推荐任何未在本地数据库记录中明确检索出的曲目。
- **杜绝 AI 幻觉**：禁止基于通用常识虚构匹配项。每条推荐必须包含真实的 `file_path`。
- **模式一致性**：Mashup 模式不得污染常规 Set 排序逻辑。

## 6. 调用示例 (Few-shot Examples)
**Input**:
- Track A: 周杰伦 - 蛇舞 (108 BPM, 2A)
- Track B: [DATABASE_SCAN] 黄立行 - 靜靜的生活 (109 BPM, 2A)
- Strategy: "Elite 3 Selection"

**Output**:
- Score: 100.0 (Elite Gold)
- Rationale: "10-BPM 黄金区，调性完美匹配。触发 Pop 对等加分。Stems 呈现乐句接龙潜力。已确认本地文件有效。"
