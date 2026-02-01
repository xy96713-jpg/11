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
- **针对截图触发 (下载)**：用户发送包含歌曲信息的截图（如播放列表、单曲封面）并附言“下载”时激活逻辑识别并提取歌名。
- **针对截图触发 (补全封面)**：当用户发送截图并说“补全封面”时，AI 提取歌曲信息，优先从网易云/iTunes 等官方音乐平台检索 1:1 高清封面并嵌入本地对应的 MP3 文件。

---

## 2. 交付标准 (The V5.4 Standard)

### A. 音质规范
- **默认格式**：MP3
- **比特率**：320kbps (CBR) / Best Available
- **来源**：YouTube Music / YouTube High Quality Audio

### B. 视觉规范 (Cover Art Protocol - V5.4 Native)
- **嵌入版本**：**必须**强制使用 **ID3v2.3**（Windows 资源管理器兼容之王）。
- **描述符 (Desc)**：APIC 帧描述符必须设为 **`'Cover'`**，否则 Windows 预览缓存可能无法抓取。
- **裁切逻辑**：**强制正方形 (1:1)** 中心裁切，分辨率推荐 **1000x1000**。
- **清洗协议**：写入前必须全量擦除旧标签 (`ID3.delete()`)，彻底杜绝 APE 或 v2.4 标签导致的灰白占位符。

### C. 路径规范
- **下载仓库**：`D:\song`
- **命名建议**：推荐使用 `Artist_Title` 格式，避免空格和中文乱码（虽然脚本支持中文）。

---

## 3. 调用协议
脚本路径：`D:\anti\技能库\02_音乐下载\assets\scripts\download_and_tag.py`
修复脚本：`D:\anti\技能库\02_音乐下载\assets\scripts\fix_covers.py`

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
