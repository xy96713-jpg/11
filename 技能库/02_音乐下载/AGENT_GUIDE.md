---
name: music_download_expert
description: 全自动音乐下载专家。支持“给歌名即下载”，自动搜索最佳音源(Mp3 320k)，并智能裁剪/嵌入正方形封面，是构建高品质本地曲库的核心工具。
---

# Music Download Expert (音乐下载与完形专家)

## 0. 核心宗旨
解决“找歌容易、整理难”的痛点。本技能不仅负责下载，更负责**“完形”**——即让每一首下载的歌曲都拥有完美的 metadata 和嵌入式封面，直接符合 Rekordbox 或 iTunes 的入库标准。

---

## 1. 触发准则 (Triggers)
当用户由以下意图时激活：
- “下载 [歌名]”
- “帮我找一下 [歌名] 的高音质版本”
- “下这首歌，要带封面的”

---

## 2. 交付标准 (The V5.4 Standard)

### A. 音质规范
- **默认格式**：MP3
- **比特率**：320kbps (CBR) / Best Available
- **来源**：YouTube Music / YouTube High Quality Audio

### B. 视觉规范 (Cover Art Protocol)
- **嵌入方式**：物理写入 ID3 `APIC` 帧（确保离线可用）。
- **裁切逻辑**：**强制正方形 (1:1)** 中心裁切。
- **意义**：防止在 CDJ 或车载屏幕上显示黑边或拉伸。

### C. 路径规范
- **下载仓库**：`D:\song\Final_Music_Official`
- **命名建议**：推荐使用 `Artist_Title` 格式，避免空格和中文乱码（虽然脚本支持中文）。

---

## 3. 调用协议
脚本路径：`D:\anti\skills\music_download_expert\scripts\download_and_tag.py`

### 基础调用：
```bash
python scripts/download_and_tag.py "周杰伦 稻香"
```

### 指定文件名调用：
```bash
python scripts/download_and_tag.py "NewJeans Ditto audio" --name "NewJeans_Ditto"
```

---

## 4. 依赖说明
- `yt-dlp`: 核心下载引擎
- `mutagen`: ID3 标签手术刀
- `Pillow (PIL)`: 图像处理与裁剪
- `ffmpeg`: 必须在系统 PATH 中可用（已确认环境具备）
