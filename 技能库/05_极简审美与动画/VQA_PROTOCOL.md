# 👁️ VQA Protocol: 强制视觉验证协议 (V6.5)

## 0. 设计初衷
为了杜绝代码端与显示端的“认知偏差”，所有涉及 **UI、图形、动画、视频** 的需求，Agent 在交付前必须执行此协议。

---

## 1. 核心准则 (Golden Rules)

1.  **见图如见面**：Agent 禁止仅凭代码猜测运行结果。必须使用 `browser_subagent` 打开网页或组件。
2.  **交互证伪**：不仅能看，还要能动。通过点击、滑动、音频输入等操作，证明组件的 **Interactive Level (交互性等级)**。
3.  **证据固化**：在 `walkthrough.md` 中必须包含带有时间戳或加红高亮的验证截图/视频。

---

## 2. 标准验证流程 (Verification SOP)

### Step 1: 环境初始化 (Initialization)
- 使用 `open_browser_url` 打开生成的视图文件。
- 确认页面资源（如 Tweakpane, CDN 库, Canvas）加载完成。

### Step 2: 状态机审计 (State Audit)
- **Idle State**: 截图证明页面打开即有内容（避免黑屏）。
- **Interaction State**: 点击特定像素或元素（如 Ignite 按钮），观察状态变化。

### Step 3: 断言与反馈 (Assertion)
- 若实际视觉与 `USER_REQUEST` 不符，Agent 必须立即进入 `FIX` 模式，不得直接交付。
- 将验证成功的截图保存至 `<appDataDir>/brain/<conversation-id>/`。

---

## 3. 结果交付规范 (Delivery Standard)

交付给用户的信息必须包含以下三要素：
- ✅ **访问链接**：指向文件的本地绝对路径。
- 📸 **实操截图**：证明当前版本已在浏览器中运行成功。
- 🎛️ **操作指引**：明确告知用户如何触发交互。

---

## 4. 强制执行范围
- 粒子系统 (Particle Systems)
- CSS/SVG 动效 (Animations)
- 可视化大屏 (Dashboards)
- 图像/视频处理脚本 (Image/Video Scripts)
认识
