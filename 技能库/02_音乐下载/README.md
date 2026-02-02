# 🎵 音乐下载专家 V8.8 (Music Download Expert)

> **金标音质保障：物理封锁 YouTube，专注高保真原声流。**

## 🌊 核心逻辑: Waterfall 全域瀑布流
本系统集成了一站式全域搜索与下载功能，自动在多个高保真平台之间进行 Waterfall 匹配：

1. **Smart Spotify Bridge**: 
   - 自动解析 Spotify 链接元数据。
   - 绕过官方 API 频率限制，实现“秒识别”。
2. **Waterfall Search (优先级)**:
   - **SoundCloud**: 首选，DJ Edits 与电音最全。
   - **Bandcamp**: 独立音乐与高保真单曲。
   - **网易云 (Netease)**: 补全，针对主流流行及中文曲目。
3. **标签完形**:
   - 自动注入 iTunes/MusicBrainz 元数据。
   - 1000x1000 高清封面嵌入，ID3 v2.3 兼容。

## 🛠️ 使用指南
运行 `scripts/download_and_tag.py` 即可触发：
```powershell
# 场景 1: 下载 Spotify 歌曲
python scripts/download_and_tag.py "https://open.spotify.com/track/..."

# 场景 2: 全网搜歌 (自动多源切换)
python scripts/download_and_tag.py "艺术家 - 歌名"
```

## 🚫 严禁事项
- **禁止使用 YouTube**: 严防低码率、MV 杂音及非原声转录。
- **禁止降质**: 所有导出强制 320kbps MP3。
