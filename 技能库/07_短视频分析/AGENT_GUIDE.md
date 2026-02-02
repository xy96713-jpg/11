---
name: short_video_analyst
description: 短视频分析专家。专门用于处理抖音/TikTok 链接，提取视频元数据、作者信息及关键帧视觉证据。
---

# Short Video Analyst (短视频分析专家)

## 1. 触发条件
- 用户发送抖音/TikTok 链接并询问“分析这个视频”。
- 用户需要提取视频文案或画面内容。

## 2. 操作流程
1. **调用脚本**: 使用 `scripts/douyin_note_taker.py`。
2. **人工辅助**: 脚本启动后，会弹出浏览器窗口。**Agent 需提示用户**：“请在弹出的窗口中协助关闭弹窗或完成验证码”。
3. **结果回收**: 分析完成后，读取输出目录下的 `note_metadata.txt` 和关键帧图片。

## 3. 注意事项
- 该技能依赖 Playwright 的 Headful 模式（有界面），因为短视频平台反爬严格，必须依赖人工或模拟真实交互。
- 默认输出目录为 `skills/07_短视频分析/output`。
