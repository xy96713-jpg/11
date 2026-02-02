# 🎵 音乐下载 (Music Download Expert)

本模块为您提供纯净、无 YouTube 杂音的高品质音乐获取方案。它集成了网易云 API、SoundCloud 解析器以及 iTunes 元数据补全引擎。

## 🌟 核心能力

- **高保真音源**：拒绝低码率 YouTube 转录，只抓取音频平台的原声流。
- **元数据自动修复**：下载后自动匹配封面、歌词、专辑名及发行日期。
- **绕过封锁**：内置代理逻辑，支持获取受限地区的优质音源。

---

## 📖 用户操作指南 (User Manual)

### 1. 怎么开始下载？
您只需发送一首歌的名字、一个歌手名或一条歌单链接。
- **SoundCloud 专线**：直接粘贴 URL，系统自动触发 `SoundCloud Agent` 极速下载。
- **普通搜索**：如 `“帮我下载 NewJeans 的 Super Shy，要高品质的”`。

### 2. 下载到哪里？
所有成品 MP3 都会统一存放在 `D:\song` 目录。

---

## 🛠️ 技术存档 (Tech Specs)
- **版本**: V8.3 (SoundCloud Agent Integrated)
- **更新时间**: 2026-02-02
- **核心组件**: 集成了原汁原味的 `soundcloud_agent.py` 模块化下载专线。
