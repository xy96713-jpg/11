---
name: music_intelligence_expert
description: 提供深度音乐智能分析、Mashup 评分维度及专业 DJ 审美指导。适用于音频特征提取、推荐算法优化及混音脚本生成等场景。
---

# 音乐智能专家 (Music Intelligence Expert)

本技能沉淀了"最强大脑"在本项目中的核心音乐逻辑，旨在确保系统始终以专业 DJ 和音频工程师的视角进行分析与推荐。

## 1. 系统架构 (System Architecture)

- **主入口**: `enhanced_harmonic_set_sorter.py` (V7.0)
- **核心引擎**: `core/` (音频分析 & 数据库连接)
- **技能模块**: `skills/` (11 个专业 Python 模块)
- **XML 导出**: `exporters/xml_exporter.py` (Rekordbox 6 写入)
- **数据资产**: `song_analysis_cache.json` (1800+ 曲目缓存)
- **运行配置**: `config/dj_rules.yaml`

## 2. 深度分析标准 (V3-PRO Dimensions)

在评估两首曲目的 Mashup 兼容性时，必须遵循以下高级维度：

- **频谱掩蔽预防**: 避免人声与伴奏在 500Hz-2kHz 重叠。
- **律动 DNA**: 确保 Straight 与 Swing 节奏不对冲。
- **动态能量曲线**: 匹配能量"同步呼吸"的段落。
- **音色纹理识别**: 审美层面的音色统一性。

## 3. 情感氛围标签库 (Deep Tags)

- **Party/Excited**: 高能量 + 积极情感。
- **Chill/Dreamy**: 低能量 + 积极情感。
- **Dark/Intense**: 高能量 + 攻击性情感。
- **Melancholy/Deep**: 低能量 + 深沉情感。

## 4. 核心排序策略 (Sorting Rules)

- **BPM 动态范围**: ±6 BPM 以内，调谐不超过 15%。
- **调性和谐度**: Camelot 同步/相邻/大小调切换。
- **低频冲突拦截**: 双高底鼓必须降权。

## 5. 后台分析守则 (Backend Rules)

- **原子化保存**: 临时文件 + Rename 确保缓存安全。
- **增量策略**: 优先读已有 bpm/key，仅补全缺失维度。
- **软件数据优先 (Metadata Lock)**: Rekordbox BPM/Key 具有绝对权重，禁止 AI 覆盖。
- **BPM 迭代纠偏**: 使用 while 循环确保落入 [65, 190] 区间。

## 6. 精准寻歌流程 (DB Indexing)

> [!IMPORTANT]
> 禁止使用 `dir /s` 全盘扫描！必须调用核心模块 `core.track_finder`。

**标准化调用方式**
```python
import sys
sys.path.insert(0, r"d:\anti\core")
from track_finder import smart_find_track

# 统一搜歌（优先 DB，自动 Fallback）
paths = smart_find_track("歌曲名关键字")
```

**原理解析 (Under the hood)**
此模块封装了 `pyrekordbox` 接口，自动完成以下步骤：
1.  查询 Rekordbox DB (`djmdContent` 表)。
2.  返回有效绝对路径。
3.  若 DB 未命中，自动扫描 `D:\song` 和 `Downloads`。
4.  自动处理文件路径编码问题。

**步骤 2: 验证文件状态**
用 `os.path.exists()` 检查路径。若不在位，再扫描 `Downloads`。

**步骤 3: 读取元数据 (精准映射)**
```python
# 必须使用 pyrekordbox 原始属性名，注意大小写
db_bpm = (song.BPM / 100.0) if hasattr(song, 'BPM') else None
db_key = song.KeyName if hasattr(song, 'KeyName') else None
```
> [!IMPORTANT]
> - `BPM`: 数据库原始值为整数（BPM * 100），必须除以 100。
> - `KeyName`: 存储 Camelot (如 11A) 或 Open Key。
> - 属性名均为 **首字母大写** (BPM, KeyName, FolderPath)。

---
---
## 7. 专家级交付协议 (Expert Delivery Protocol V5.4)

> [!IMPORTANT]
> **标点可见性保障**：为防止 Rekordbox 缓存导致 Hotcues 丢失，必须执行以下操作：
> 1. **物理复制**：音频必须镜像至 `D:\生成的set\audio\`。
> 2. **元数据装饰**：Title 强加 `✅[AI_FULL_V5.4]` 标识。
> 3. **ID 同步**：优先从 DB 继承 `TrackID`。

> [!TIP]
> 当用户询问"如何提升 Mashup 质量"时，请始终参考频谱掩蔽及律动对齐标准。
