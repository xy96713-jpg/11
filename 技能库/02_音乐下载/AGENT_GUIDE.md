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
- “下载 [歌名/链接]”
- “帮我找一下 [歌名] 的高音质版本”
- “下这首歌，要带封面的”

---

## 2. 交付流程规范 (The V8.8 Standard)

本系统遵循**“全域瀑布流聚合”**准则，严禁使用视频转录资源。

### 轨道 A: 智能链接桥接 (Smart Links)
- **Spotify**: 自动通过 OG (OpenGraph) 元数据解析 ID 并转为文本查询。绕过 API 限制。
- **SoundCloud**: 保留 `soundcloud_agent.py` 专线，直接提取原声流。

### 轨道 B: 瀑布流搜索 (Waterfall Search)
- **核心逻辑**: **SoundCloud -> Bandcamp -> Netease (163)**。
- **严禁事项**: **禁止调用 YouTube** (严防低码率、MV 杂音)。
- **强制完形**: 集成 iTunes API 与 MusicBrainz，强制嵌入 1000x1000 高清封面，导出 ID3 v2.3。

### 轨道 C: 封面智理 (Agentic Cover Intel)
- **Agent Vision**: 当接收到截图，应调用视觉模型定位 `NewJeans - ETA` 等关键词。
- **Local Fidelity**: 搜索封面时，必须优先检索 `D:\song`，如存在同名 `.png` 或 `_cover.png`，严禁转码，直接拷贝以保留原图最高清晰度。
- **Standalone Mode**: 如用户仅需封面，调用 `standalone_cover_extractor.py`。

---

## 3. 调用协议 (Modular Core)
- `download_and_tag.py`: V8.8 统一调度分发器 (实现 Waterfall 逻辑)。
- `soundcloud_agent.py`: SoundCloud 专用高速接口。
- `spotify_agent.py`: 备用 spotDL 桥接引擎 (优先使用主脚本的 Smart Bridge)。

---

## 4. 为什么不用 YouTube？
本技能坚守 **“非视频转录”** 金标（V8.6 Gold Standard）。YouTube 音频存在码率虚标、MV 杂音及声场压缩等致命问题。

## 5. 常见维护指令
- 提取封面: `python scripts/standalone_cover_extractor.py "关键词" --output "D:\视频文件\视频图片"`
- 更新元数据: `python scripts/perfect_metadata.py <文件路径>`
