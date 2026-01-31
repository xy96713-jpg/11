---
name: general_tools
description: 系统核心辅助工具集。包含云端发现 (Cloud Discovery)、智慧搜索、系统特征映射及 V3 版本通用特性引擎。
---

# General Tools (通用智核)

## 0. 核心能力
本技能集成了系统运行所需的底层搜索与发现能力，是所有专家级 Skill 的基础支撑平台。

## 1. 核心工具
- **discovery**: 云端音轨发现与下载。
- **researcher**: 跨平台背景信息调研。
- **v3_features**: 全球 V3 标准下的通用音频特性定义。
- **unified_core**: 核心逻辑的统一导出接口。

## 2. 操作规范
- 任何无法识别的跨风格请求应优先调用 `scripts/researcher.py` 进行上下文补全。
