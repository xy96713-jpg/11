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

## 2. 交付标准 (The V8.3 Standard)

### A. 音质规范
- **默认格式**：MP3
- **比特率**：320kbps (CBR)
- **SoundCloud (优先)**：强制通过 `SoundCloud Agent` 专线下载，确保原始高音质。
- **YouTube (兜底)**：仅当通用搜索触发时使用，通过 `yt-dlp` 转换为最高品质 MP3。

### B. 视觉规范 (Cover Art Protocol)
- **嵌入方式**：物理写入 **ID3 v2.3** 帧（最稳兼容 Windows/Rekordbox）。
- **来源逻辑**：
  - **SoundCloud**: 提取官方 `original` 级别高清封面。
  - **通用模式**: 优先检索 iTunes API (1000x1000)，兜底 MusicBrainz。
- **裁切逻辑**：强制正方形 (1:1) 中心裁切，拒绝拉伸。

### C. 路径规范
- **下载仓库**：`D:\song` (标准入口)
- **整理脚本**: `D:\anti\技能库\02_音乐下载\scripts\download_and_tag.py`

---

## 3. 调用协议

### SoundCloud 专线 (自动识别):
系统会自动识别 SoundCloud 链接并挂载 `soundcloud_agent.py`。
```bash
python scripts/download_and_tag.py "https://soundcloud.com/..."
```

### 通用搜索下载:
```bash
python scripts/download_and_tag.py "歌名 歌手"
```

---

## 4. 核心组件 (Modular Core)
- `soundcloud_agent.py`: 专线调度中心。
- `ultra_fast_download.py`: 并行加速与封入引擎。
- `download_mp3_with_cover.py`: 兼容性下载保障。
- `download_and_tag.py`: 统一入口。
