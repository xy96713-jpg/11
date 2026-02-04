---
name: 🎵 字幕与歌词生成专家 (Subtitle & Lyricist)
description: 专注于基于音频流的精确时间轴转录与歌词同步 (Whisper + Demucs Pipeline)。
version: 1.0 (2026 Alpha)
author: Antigravity Core
triggers:
  - /lyric
  - /srt
  - "生成字幕"
  - "提取歌词"
dependencies:
  - faster-whisper
  - torch (CUDA recommended)
  - demucs (optional, for music)
---

# 🎵 Skill 10: 字幕与歌词生成专家

本技能模块基于 OpenAI 的 Whisper 架构（Faster-Whisper 实现）与 Demucs 分离算法，提供工业级的音频转录与时间轴对齐服务。

## 的核心能力 (Core Capabilities)

1.  **高精转录 (Hi-Fi Transcription)**:
    - 使用 `faster-whisper-large-v3` 模型，支持 99 种语言。
    - 自动识别标点、断句与说话人切换。

2.  **强制对齐 (Forced Alignment / LRC Generation)**:
    - 输出毫秒级精度的 `.lrc` (歌词模式) 或 `.srt` (字幕模式)。
    - **Music Mode**: 自动检测音乐，先通过 Demucs 剥离人声，再进行转录，避免 BGM 干扰。

3.  **多格式支持**:
    - Input: `mp3`, `wav`, `flac`, `m4a`, `mp4` (自动提取音轨)
    - Output: `filename.lrc`, `filename.srt`, `filename.json` (raw data)

## 🛠️ 使用指南 (Quick Start)

### 1. 安装依赖 (Environment Setup)
```bash
pip install -r requirements.txt
# 确保安装了 ffmpeg (System Path)
```

### 2. 运行指令
```bash
# 标准模式 (适合对话/播客)
python lyric_engine.py "D:\downloads\interview.mp3"

# 音乐模式 (自动分离人声，适合歌曲)
python lyric_engine.py "D:\music\NewJeans_OMG.mp3" --mode song
```

## ⚙️ 专家协议 (Protocols)

### Protocol 10.1: Music Separation Mandate
> **规则**: 如果检测到输入为歌曲 (Song) 或 BGM 嘈杂，**必须**先运行 Demucs 分离出 `vocals.wav`。
> **理由**: Whisper 在强背景音乐下极易产生 "Hallucination"（幻觉），胡乱生成歌词。

### Protocol 10.2: Timestamp Granularity
> **规则**: 歌词 (LRC) 必须精确到行 (Line-Level)，且每行时间戳不得重叠。
> **格式**: `[mm:ss.xx] Lyric content`

### Protocol 10.3: Performance Awareness
> **提示**: 默认加载 `medium` 或 `large` 模型。如果检测到无 CUDA 环境，自动降级为 `small` 或 `int8` 量化模式以保护 CPU。
