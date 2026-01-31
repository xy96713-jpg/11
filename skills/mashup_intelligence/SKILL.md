---
name: mashup_intelligence
description: 音乐混音智能匹配引擎 (V7.0)。涵盖 BPM 比例弹性匹配、文化 DNA 共鸣、音频频谱特征检测及全方位混音评分算法。
triggers: ["寻找混音搭档", "mashup", "匹配度分析", "banger discovery"]
---

# Mashup Intelligence (混音智核)

## 0. 核心能力
本技能提供专家级的歌曲匹配评分，支持跨曲风、跨速度的深度律动分析。其核心算法基于 11 个音频维度进行加权计算。

## 1. 算法特征 (Algorithm Hooks)
- **BPM 混合比例**：支持 1:1, 3:4, 2:3, 1:2 等多种律动嵌套。
- **文化 DNA 识别**：识别采样渊源、乐器音色（如采样自 Jay Chou 或 Western Trap）。
- **频谱平衡度**：检测 Mid/High 频率分布，防止混音重叠。

## 2. 调用说明
调用 `scripts/core.py` 中的 `calculate_mashup_score` 进行两首曲目的全量比对。

## 3. 使用场景
- 需要为“忍者”或“双截棍”寻找西方 Trap/Hip-hop 伴奏时。
- 需要进行高能量 Peak time 混音排列时。

## 4. 调用示例 (Few-shot Examples)
**Input**:
- Track A: 周杰伦 - 忍者 (105 BPM, 4A)
- Track B: Kendrick Lamar - DNA (140 BPM, 4A)
- Strategy: "Banger Discovery"

**Output**:
- Score: 88.5
- Rationale: "3:4 BPM 比例完美契合，调性一致，文化 DNA 均含高频打击乐采样。触发 +15.0 Banger Bonus。"
