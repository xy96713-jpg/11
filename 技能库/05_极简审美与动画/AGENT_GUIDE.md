# Skill: 万能视频感知引擎 (Universal Video Perception Engine V6.1)

## 0. 核心定位
本 Skill 专为**高对抗、高动态**的视频平台（以抖音为代表）设计。它不依赖传统的页面解析，而是通过 **CDP (F12) 流量监听** 与 **本地多模态还原**，实现对视频内容的“全量复刻”。

---

## 1. 核心链路 (Workflow)

### A. 智能路由 (Routing)
- **抖音入口**：识别 `douyin.com`，强制进入 `wiretap_video.py` 监听模式。
- **通用入口**：使用 `yt-dlp` 进行标准抓取。

### B. “天眼”拦截 (Interception)
- 利用 `Playwright` 启动持久化环境。
- 监听 `aweme/v1/web/aweme/detail` API，抓取未经过滤、带签名的 **CDN 直接地址** 和 **官方 AI 元数据**。

### C. 全谱还原 (Reconstruction)
- **ASR**：调用本地 `OpenAI Whisper`，获取 1:1 讲解文本。
- **OCR**：调用本地 `RapidOCR`，提取硬字幕，补足 ASR 同音字。
- **视觉**：通过画面熵值动态采样，自动捕捉关键帧。

---

## 2. 操作指南 (Usage Guide)

### 一键式调用
在 Terminal 执行以下命令：
```powershell
$env:HOME = 'C:\Users\Administrator'; python D:\anti\skills\douyin_intelligence\scripts\video_intel_master.py "[目标链接]" "D:\anti\downloads\analysis_result"
```

### 结果产出
- **视频原片**：无水印、最高清 CDN 镜像。
- **`full_spectrum_truth.json`**：全量语音/字幕文本流。
- **`frames_v6/`**：关键技术截图库。

---

## 3. 规范约束 (Constraints)
1. **防爆处理**：强制将文件名重命名为 `ASCII/简洁中文`，避免 FFmpeg 因特殊字符（如 🐰、#）报错。
2. **Token 策略**：严禁将原始视频帧大量上传至云端 LLM，必须先在本地进行 OCR 过滤或熵值采样。
3. **环境依赖**：必须确保 `$env:HOME` 指向正确的 Playwright Root，否则浏览器无法初始化。
