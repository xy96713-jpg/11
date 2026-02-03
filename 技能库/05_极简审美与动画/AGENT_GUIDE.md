# 视觉与动态实验室 (Visual & Dynamic Lab) - Agent Guide

本模块是 Antigravity 的**视觉中枢**，整合了审美、UI 设计与 3D 可视化三大核心能力。

## 0. 核心定位
将“好用”升级为“惊艳”。本模块不产生平庸的 UI，只产生具有电影质感和流动生命的交互体验。

---

## 1. 组合方案 (Modular Combination)

| 阶段 | 负责人 | 核心职责 | 参考指南 |
| :--- | :--- | :--- | :--- |
| **Stage 1: 审美/动效** | `05_aesthetic_core` | 确定调色盘、定义粒子/GSAP 动效基调 | [Aesthetic Guide](./05_aesthetic_core/AGENT_GUIDE.md) |
| **Stage 2: 界面/架构** | `08_premium_ui` | 构建 React/Next.js 高级组件、Bento 布局 | [Premium UI SKILL](./08_premium_ui/SKILL.md) |
| **Stage 3: 3D/升华** | `09_3d_visualizer` | 注入 Three.js/WebGL 元素、3D 数据可视化 | [3D Visualizer SKILL](./09_3d_visualizer/SKILL.md) |

---

## 2. 统一工作流 (Unified Workflow)

当用户提出视觉需求（如：“做一个高级的 3D 数据仪表盘”）时，遵循以下链路：

1.  **审美推演 (Moodboard)**:
    *   锁定关键词（赛博朋克、极简、流体等）。
    *   定义 HSL 配色方案（严禁默认红蓝）。
2.  **界面构建 (Architecture)**:
    *   使用 `08_premium_ui` 中的高级组件模板（如 Glassmorphism）。
    *   确保响应式布局与极简交互。
3.  **动态注入 (Dynamics)**:
    *   注入 `05_aesthetic_core` 的粒子系统或微动效。
    *   根据需求引入 `09_3d_visualizer` 的 3D 场景或 Three.js 背景。
4.  **VQA 强制验证**:
    *   必须使用 `browser_subagent` 预览并截屏。
    *   验证在多种分辨率下的视觉表现、性能及交互反馈。

---

## 3. 操作禁令 (Constraints)
- **拒绝 AI 塑料感**: 严禁使用过于饱和的渐变和默认字体（如 Inter）。必须选用 `08_premium_ui` 推荐的字体组合。
- **性能优先**: 3D 元素必须通过 `requestAnimationFrame` 优化，并提供降级方案。
- **画廊归档**: 每一个成功的视觉生成物必须同步至 `gallery/` 目录并更新索引。
