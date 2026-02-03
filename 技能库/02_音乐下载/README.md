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
4. **封面智理 (Agentic Cover Vision)**:
   - **截图识别**: 智能体视角下发截图，自动提取歌名并批量导出封面。
   - **本地优先**: 搜索逻辑首选 `D:\song` 本地原档（Remix/Edit 版），保留 PNG 高码率原图。
   - **多源备份**: 本地找不到时自动切换 iTunes API (1000x1000) -> YouTube (4K Thumbnail)。

## 🛠️ 使用指南
运行 `scripts/download_and_tag.py` 或 `scripts/ultra_fast_download.py` 即可触发：
```powershell
# 场景 1: 音频下载 (同步保存封面)
python scripts/ultra_fast_download.py "<链接>" --save-cover

# 场景 2: 独立封面提取 (支持本地/关键词/URL)
# 默认输出至当前目录，支持模糊匹配本地库
python scripts/standalone_cover_extractor.py "艺术家 - 歌名" --output "D:\视频文件\视频图片"

# 场景 3: 截图提取 (智能助手专供)
# 直接将截图投喂给智能助手，口令：“提取封面”
```

## 🚫 严禁事项
- **禁止降质**: 所有导出强制 320kbps MP3。
- **格式保护**: 提取本地封面时，严禁强制转换格式（保留 PNG 高清原件）。
