# 📉 短视频智能分析 (Short Video Intelligence)

> **核心功能**: 针对抖音/TikTok 视频进行深度分析、元数据提取及关键帧截取。

## 1. 功能特性
- **交互式采集**: 启动有头浏览器，允许用户手动处理验证码或登录（Playwright）。
- **元数据提取**: 自动抓取视频简介 (Description)、作者 (Author) 等信息。
- **视觉采样**: 自动截取 `00s`, `05s`, `15s`, `End` 四个时间点的关键帧，用于后续分析。

## 2. 使用方法

### 基础调用
```powershell
python scripts/douyin_note_taker.py "https://v.douyin.com/..."
```

### 指定输出目录
```powershell
python scripts/douyin_note_taker.py "URL" "D:\my_analysis_output"
```

## 3. 输出产物
- `note_metadata.txt`: 包含作者与简介文本。
- `note_thumb_*.png`: 关键帧截图证据。

## 4. 依赖
- Python 3.8+
- `playwright` (需运行 `playwright install`)
