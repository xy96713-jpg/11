---
description: 启动“全域解决方案 (Skill 06)”对复杂问题进行全网搜集与多方案对比
---

# 🛡️ 全域解决方案工作流 (Solve Workflow)

当用户输入 `Solve:`、`全面搜索`、`给个方案` 或提出涉及“调研/对比/评估”的需求时，**必须**执行以下步骤：

## 1. 技能库对齐 (Skill Alignment)
- **必选动作**：读取 `d:/anti/技能库/06_全域解决方案/SKILL.md` 以获取最新的 SOP。

## 2. 搜索三位一体 (The Search Triad)
// turbo
1. **MCP 扫描**: 运行 `npx -y skills find [关键词]` 检查 `skills.sh` 插件。
2. **GitHub 扫描**: 搜索 `site:github.com [关键词] stars:>500`。
3. **社区扫描**: 搜索 `[关键词] best practices 2024` 或对比方案。

## 3. 评估与交付 (Assessment & Delivery)
- 构建对比矩阵（MCP vs 开源库 vs 原生）。
- 输出至 `current_research.md`。
- **最终结论**: 给出唯一确定的 Recommended 方案。

---
*注：此工作流是系统的“硬路由”，优先级高于 Agent 的通用搜索。*
