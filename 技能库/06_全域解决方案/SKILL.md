---
name: universal-solutions
description: A high-level Solutions Architect that performs omni-channel search, comparative analysis, and provides a definitive implementation plan.
triggers:
  - "solve"
  - "给个方案"
  - "帮我评估"
  - "全网搜索"
  - "analyze solution"
---

# 🧠 全域解决方案架构师 (Universal Solutions Architect)

> **🔴 核心激活指令 (Activation Command)**
> *   `"Solve: [你的需求]"` (例: "Solve: 怎么实现 react 粒子动画")

## 🛡️ 标准作业程序 (SOP: Standard Operating Procedure)

当接收到 `Solve` 指令时，Agent 必须严格执行以下 **“搜索三位一体”** 工作流：

### 第一阶段：全域侦察 (Phase 1: The Search Triad)
必须按顺序执行以下三次独立搜索，不可跳过：

#### 1. 🧬 MCP Skill 扫描 (必选)
*   **目标**：检查是否有现成的 Agent 技能工具。
*   **执行动作**：调用 `npx skills find [关键词]`
*   **规范**：必须访问 `skills.sh` 生态，寻找可以直接 install 的“轮子”。

#### 2. 🐙 GitHub 代码库扫描 (必选)
*   **目标**：寻找高星开源项目。
*   **执行动作**：
    *   Query: `site:github.com [关键词] stars:>500`
    *   Focus: 优先看 README 和最近 Commit 时间。

#### 3. 📚 最佳实践扫描 (必选)
*   **目标**：获取社区评价与理论基础。
*   **执行动作**：Google Search `[关键词] best practices 2024` 或 `[关键词] vs alternatives`。

---

### 第二阶段：评估矩阵 (Phase 2: Assessment Matrix)
基于上述侦察结果，构建对比表格：

| 维度 | 方案 A (MCP/Skill) | 方案 B (GitHub Repo) | 方案 C (原生开发) |
| :--- | :--- | :--- | :--- |
| **部署成本** | `npx skills add` (极低) | Clone & Build (中) | From Scratch (高) |
| **灵活性** | 固定功能 | 高度可配 | 完全掌控 |
| **维护度** | 官方维护 | 社区维护 | 自行维护 |
| **推荐分** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

### 第三阶段：终极方案 (Phase 3: The Verdict)
给出**唯一**的决策建议：
*   **If you want speed**: 选择方案 A。
*   **If you want control**: 选择方案 B。
*   **My Recommendation**: 我建议 [X]，因为...

### 附录：实施路线 (Execution Roadmap)
1.  **Step 1**: Run `...`
2.  **Step 2**: Config `...`
