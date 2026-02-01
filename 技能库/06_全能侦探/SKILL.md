---
name: universal-detective
description: A unified search expert that finds tools, skills, and code repositories across GitHub and the MCP ecosystem.
triggers:
  - "find a skill"
  - "search github"
  - "找个工具"
  - "搜索仓库"
  - "find repo"
---

# 🕵️‍♂️ 全能侦探 (Universal Detective)

> **🔴 核心激活指令 (Activation Triggers)**
> *   **找能力/Skill**：`"帮我找个能做 [功能] 的技能"` / `"Find a skill for [Feature]"`
> *   **找代码/Repo**：`"搜一下 GitHub 上的 [关键词] 项目"` / `"Search GitHub for [Query]"`
> *   **找解决方案**：`"有没有现成的工具可以处理 [问题]?"`

## 🧠 技能概述
本模组整合了 **MCP Skill Hunter** 和 **GitHub Deep Search** 双重能力，是您探索开源生态的雷达。

## 🛠️ 能力列表

### 1. 技能猎手 (Skill Hunter)
*   **源**：`skills.sh` (MCP Ecosystem)
*   **用途**：当您需要扩展 Agent 能力时（如：浏览器操作、数据库连接、飞书集成）。
*   **指令示例**：
    *   `npx skills find browser` (查找浏览器相关技能)
    *   `npx skills add [package]` (安装技能)

### 2. 代码侦察 (Code Scout)
*   **源**：GitHub API
*   **用途**：寻找具体的开源项目、代码片段或解决方案。
*   **逻辑**：
    *   自动过滤 Stars < 100 的低质项目。
    *   优先推荐近 1 年有 Update 的活跃仓库。
    *   支持 `lang:python` 等高级过滤语法。

## 🤖 自动工作流
当用户提出模糊需求（如“我想做个像 NewJeans 那样的粒子效果”）时：
1.  优先在 **GitHub** 搜索相关图形库（`canvas-particles`, `interactive-bg`）。
2.  同时检索 **MCP Skills** 看是否有现成的视觉生成工具。
3.  输出综合推荐列表。
