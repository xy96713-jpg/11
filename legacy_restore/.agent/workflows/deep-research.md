---
description: 如何启用“深度研究 (Deep Research)”模式协助用户分析复杂课题
---

# 🚀 深度研究工作流 (Deep Research Workflow)

当用户要求“深度研究”、“全方位分析”或“替代 NotebookLM”时，请执行以下步骤：

1. **环境确认**：
   - 确认云端 API 可用，无需关注本地 IP。
   - 检查 `d:\anti\ultra_browser_agent.py` 是否存在。

2. **自主探索**：
   - 调用 `search_web` 获取第一批关键词结果。
   - 使用 `browser_subagent` 进入高权重网站（如 GitHub, Arxiv, 行业媒体）进行深度阅读。

3. **知识合成**：
   - 提取各方观点，建立矛盾校对。
   - 生成具有 `implementation_plan` 深度的数据综述。

4. **成果输出**：
   - 输出至 `current_research.md` 供用户审阅。
   - 关键结论必须加粗并建立置信度评级。

// turbo
5. **执行握手测试**：
   `python d:\anti\final_ai_handshake.py`
