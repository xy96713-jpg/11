---
name: music_download_expert
description: 全自动音乐下载专家。支持“给歌名即下载”，自动搜索最佳音源(Mp3 320k)，并智能裁剪/嵌入正方形封面，是构建高品质本地曲库的核心工具。
---

# Music Download Expert (音乐下载与完形专家)

## 0. 核心宗旨
解决“找歌容易、整理难”的痛点。本技能坚持**“高保真、非录屏”**准则，严禁抓取 YouTube 转录音频，确保每一首下载的歌曲都是源自 SoundCloud/网易云等音频平台的原声流，并由 V8.4/V8.6 标准完成“元数据完形”。

---

## 1. 触发准则 (Triggers)
当用户由以下意图时激活：
- “下载 [歌名]”
- “帮我找一下 [歌名] 的高音质版本”
- “下这首歌，要带封面的”

---

### A. 音轨规范
- **默认格式**：MP3 (320kbps)
- **绝对屏蔽**：**YouTube (严禁作为音源)**。
- **首选源**：SoundCloud (链接或搜索)。
- **辅助源**：网易云音乐 / Bandcamp / Apple Music (仅链接直连)。

### B. 核心交付规范
- **音质**: 强制 320kbps MP3。
- **视觉**: 强制 **ID3 v2.3** + 正方形高清封面。
- **封面来源策略 (优先级降序)**:
    1. **本地检索**: 优先扫描 `D:\视频文件\视频图片` 寻找匹配的 `.jpg` 或 `.png`。
    2. **格式转换**: 若本地为 `.png`，自动转换为高品质 `.jpg`。
    3. **联网补全**: 仅在本地无匹配时，通过 iTunes/MusicBrainz 联网下载。
- **存储**: 音频统一落盘于 `D:\song`。

---

## 3. 调用协议
### 基础调用 (SoundCloud 专用):
当传入 SoundCloud URL 时，系统会自动调用底层的 `soundcloud_agent.py` 进行并行下载与封面注入。

```bash
python scripts/download_and_tag.py "https://soundcloud.com/..."
```

### 基础调用 (通用搜索):
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
