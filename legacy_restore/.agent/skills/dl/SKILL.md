---
name: music_download_expert
description: 专业音乐下载与元数据处理技能。支持从SoundCloud、网易云获取高品质音源，自动注入iTunes/MusicBrainz高清封面与ID3标签。严格遵循"非YouTube"策略。
---

# 音乐下载专家 (Music Download Expert) V7.1

本技能提供一站式音乐下载解决方案，支持批量下载、高清封面获取、ID3标签自动注入。

## 1. 触发条件 (Triggers)

当用户需求包含以下场景时，应激活本技能：
- 下载指定歌曲/歌单
- 补充缺失的封面或元数据
- 从截图/歌单识别并批量下载

## 2. 核心功能 (Core Features)

### 2.1 下载引擎
```bash
# 单曲下载 (from SoundCloud)
python scripts/download_and_tag.py "艺术家 歌名" --name "文件名"

# 批量下载 (from list file)
python scripts/batch_download.py --limit 10
```

### 2.2 多源封面策略 (Cover Art Fallback)
1. **iTunes API** - 1000x1000 官方封面
2. **MusicBrainz/Cover Art Archive** - 500px+ 高清封面
3. **视频缩略图** - 最后备选

### 2.3 修复缺失封面
```bash
# 为指定文件补上封面
python scripts/fix_missing_covers.py
```

## 3. 技术规格 (Specifications)

| 项目 | 规格 |
|------|------|
| 输出格式 | MP3 320kbps |
| 封面分辨率 | 1000x1000 (正方形裁剪) |
| ID3 版本 | v2.3 |
| 输出目录 | `D:\song\Final_Music_Official` |

## 4. 依赖 (Dependencies)

```
yt-dlp
mutagen
Pillow
musicbrainzngs
requests
ffmpeg (system)
```

## 5. 文件结构 (File Structure)

```
dl/
├── SKILL.md           # 本文件
└── scripts/
    ├── download_and_tag.py      # 核心下载脚本
    ├── batch_download.py        # 批量下载
    ├── fix_missing_covers.py    # 封面修复
    └── export_cookies.py        # Cookie导出
```

## 6. 严格非YouTube策略 (No-YouTube Policy)

> [!IMPORTANT]
> 本技能已完全屏蔽YouTube搜索与提取器。
> - `block_extractors: ['youtube', 'youtube:tab', 'youtube:playlist', 'youtube:search']`
> - 仅使用 SoundCloud 搜索 (`scsearch1:`)

## 7. 快速使用示例

**场景：用户提供截图，要求下载歌曲**
1. 识别截图中的歌曲信息
2. 调用 `download_and_tag.py` 逐一下载
3. 检查封面，如有缺失调用 `fix_missing_covers.py`

**场景：批量下载歌单**
1. 将歌单保存为 `song_list.txt` (每行一首：艺术家 - 歌名)
2. 运行 `batch_download.py`

> [!TIP]
> 若封面获取失败，可尝试增加搜索关键词或使用英文名搜索。
