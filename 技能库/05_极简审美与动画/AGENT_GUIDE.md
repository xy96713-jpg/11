# 视觉与动态实验室 (Visual & Dynamic Lab) - Agent Guide

本模块是 Antigravity 的**视觉中枢**，整合了审美、UI 设计与 3D 可视化三大核心能力。

## 0. 核心定位
将“好用”升级为“惊艳”。本模块不产生平庸的 UI，只产生具有电影质感和流动生命的交互体验。


---

## ⚡ 协议 0: 内核集成 (Kernel Integration)
本技能已进化为 **三位一体集成模组**。在启动任何任务前，必须根据任务等级（Tier）激活内部智脑：

### 1. 审计分级制度 (Tiered Audit)
- **L1 (微操级)**: 如修改 CSS 颜色、微调文字。
    - **执行**: Builder 直接动手，事后进行 VQA 截屏验证。
- **L2 (组件级)**: 如创建静态 UI 卡片、重构简单 JS。
    - **执行**: 强制通过 **Inner Arch (Skill 09)** 进行鲁棒性与性能审计，无需 PM 预审。
- **L3 (系统级)**: 如开发新动效、构建多模态 UI。
    - **执行**: **全量启动**。PM 确定审美调性 -> Arch 审计物理数学与性能配置 -> Builder 最终代码。

### 2. 性能预算锁 (Performance Budget)
- **强制 144Hz**: 任何动效代码必须在 Inner Arch 阶段进行“掉帧预演”。
- **GPU 压力管控**: WebGL/Canvas 渲染必须包含降级逻辑，性能开销严禁超过系统级阈值的 30%。

### 3. 反向反馈制衡 (Reverse Feedback Loop)
- **Builder 否决权**: 如果 Builder 在实现过程中发现 PM 定义的审美（如流体材质）在当前引擎下必掉帧，**必须反向质疑**。
- **动作**: 触发“架构再协商”，强制 PM 降级审美或 Arch 优化算法，直到满足“惊艳且流畅”的双重红线。

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
