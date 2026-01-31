---
name: cueing_intelligence
description: 专家级标点 (Hotcue) 生成系统。支持 V3 乐句语义分析、Pro-Level 混音点识别、人声感知剪辑及物理网格 PQTZ 量化。
---

# Cueing Intelligence (标点智核)

## 0. 核心能力
本技能负责音频音轨的结构化分析，自动生成符合 DJ 演奏逻辑的 Hotcue (A-H) 以及 Memory Cues。

## 1. 子模块组件
- **v3**: 核心乐句/能量段落识别。
- **pro**: 针对专业混音场景的点位推荐。
- **vocal**: 人声存在探测，防止在人声叠加处进行切入。

## 2. 操作规范
- 必须调用 `scripts/v3.py` 进行基础结构扫描。
- 必须确保所有点位通过 `PQTZ` 协议完成毫秒级对齐。

## 3. 使用场景
- 新曲库入库后的自动打点。
- 自动化生成带标点的 XML 播放列表。
