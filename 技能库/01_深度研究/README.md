# 🧠 深度研究 (Deep Research & NotebookLM Aligned)

本模块是您环境中的“最强大脑”，旨在彻底替代并超越受限的 NotebookLM 体验。它通过自动化浏览器与长上下文 AI 协同，实现全网知识的实时内化。

## 🚀 核心核心 (NotebookLM 级能力)

### 1. 🌐 全网知识源集成 (Multi-Source Ingestion)
- **超越静态 PDF**：NotebookLM 只能读您上传的文件，**我们能读整个互联网**。
- **动态抓取**：自动抓取 GitHub 源码、Arxiv 论文、YouTube 脚本（仅文本）以及行业实时新闻。
- **环境伪装**：内置 `us-proxy` 级联逻辑，确保即便在受限区域也能调取全球顶尖信源。

### 2. 📝 智能摘要与脑图生成 (Synthesis & Mapping)
- **长文档粉碎机**：一次性处理 100k+ token 的复杂文档，提取核心矛盾点与共识点。
- **多维综述**：自动生成 implementation_plan 或深层技术调研报告。

### 3. 💬 闭环问答控制台 (Closed-Loop Q&A)
- **事实审计**：所有回答均带原文链接，杜绝 AI 幻觉。
- **深度溯源**：点击报告中的结论可直接定位至原始网页或 assets/ 中的缓存文件。

---

## 📖 给您看的操作指南 (User Manual)

- **如何触发研究？**
  - 在对话框直接输入：`“帮我深度研究 [课题名/URL/文件]”`
  - 或者使用更进阶的需求：`“用 [深度研究] 模块对比 [A产品] 和 [B产品] 的底层架构差异”`
- **查看结果**：
  - 我会在根目录为您生成 `current_research.md`。
  - 核心资产和缓存会保存在 `assets/` 中供您随时查阅。

## 🤖 给 AI 看的接入规范 (Agent Protocol)

- **调用入口**：执行 `assets/ultra_browser_agent.py` 或调用 `AGENT_GUIDE.md` 中的工作流。
- **环境要求**：必须先运行 `🛠️ 系统工具` 中的环境激活脚本，确保 `Remote Debugging Port 9222` 已开启。

---

## 🛠️ 技术存档 (Tech Specs)
- **版本**: V2.8 (NotebookLM Aligned Edition)
- **驱动引擎**: Playwright + Gemini Pro 1.5 (Cloud)
- **更新时间**: 2026-01-31

> [!TIP]
> **想要复刻 NotebookLM 的“对话笔记”感？**
> 只需对我说：“建立关于 [课题] 的研究笔记”，我会自动开启全网搜集并在 `assets/` 下为您建立知识库索引。
