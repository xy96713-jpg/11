---
name: rekordbox_xml_intelligence
description: Rekordbox XML 深度集成与智能标点标准。涵盖 A-H 全量标点定义、Windows 路径兼容性协议、物理元数据注入及 PQTZ 量化准则。
---

# Rekordbox XML Intelligence (RB 智能集成专家 V7.5)

## 0. 核心宗旨
本技能库旨在规范 AI 与 Rekordbox 之间的数据交换协议，确保所有生成的 HotCue、Memory Cue 及 XML 播放列表在物理层和逻辑层均能 100% 被 Rekordbox 正确解析。V7.5 强化了防撞车逻辑与残差报告。

---

## 1. 全量标点等级标准 (The HotCue Standard V5.4)

所有标点必须严格遵循以下色彩与功能映射标准，严禁随意分配：

| HotCue | 功能定义 | 建议颜色 | 物理特征 |
| :--- | :--- | :--- | :--- |
| **A** | `[IN] START` | 蓝色 (0x0000FF) | 进歌窗起点，毫米级量化 |
| **B** | `[IN] DONE` | 黄色 (0xFFFF00) | Intro 结束，主乐句/Verse 开始 |
| **C** | `[OUT] START` | 蓝色 (0x0000FF) | 建议混音出点，由 Sorter/Outro 决定 |
| **D** | `[OUT] END` | 蓝色 (0x0000FF) | 歌曲物理结束/淡出点 |
| **E** | `[DROP] PEAK` | 红色 (0xFF0000) | 第一高潮点，通过物理波形/Phrase 定位 |
| **F** | `[VERSE/CHORUS]` | 红色 (0xFF0000) | 结构转折/第二高潮点 |
| **G** | `[BRIDGE]` | 青色 (0x00FFFF) | 间奏/Bridge/大桥位置 |
| **H** | `[LINK] -> NEXT` | 绿色 (0x00FF00) | **下曲连通门**，基于下一曲导入长度计算 |

> [!IMPORTANT]
> **Memory Cues (Num="-1")**：必须在 H 点位注入详细的混音建议，如 `"MIX: 与下一曲 32 拍对齐"`。

---

## 2. Windows 兼容性 XML 导出协议 (The Compatibility Protocol)

为防止 Rekordbox 出现“文件损坏”、“无法分析”或“路径丢失”，XML 必须满足以下物理条件：

### A. 路径 Location 编码
- **协议格式**：必须使用 `file://localhost/D:/path/file.mp3`。
- **盘符处理**：盘符必须大写，且冒号 `:` 禁止编码为 `%3A`。
- **路径处理**：使用 `pathlib.Path.as_uri()` 为基准，并将 `file:///` 替换为 `file://localhost/`。

### B. 关键物理属性注入
- **Size**：必须通过 `os.path.getsize()` 读取真实的字节数。
- **TotalTime**：必须注入真实音频时长（秒）。
- **注意**：若上述两项为 0，Rekordbox 6+ 会拒绝导入或分析。

---

## 3. 专家级物理隔离导出协议 (The Expert Isolation Protocol V5.4)

为 100% 解决“看不到标点”及“重复分析”顽疾，导出逻辑必须遵循以下物理隔离准则：

### A. 物理路径重定向 (Physical Redirection)
- **准则**：禁止直接引用原始曲库路径！
- **操作**：必须将音轨物理复制到隔离目录（如 `D:/生成的set/audio/[Playlist]/`）。
- **目的**：通过物理路径变动强制 Rekordbox 建立全新的数据库记录。

### B. 视觉装饰与元数据脱钩 (Metadata Decoration)
- **Title 装饰**：曲目标题必须添加 `✅[AI_FULL_V5.4]` 后缀。
- **Artist 装饰**：艺术家名必须添加 `[VERIFIED_BY_ANTIGRAVITY]` 后缀。
- **目的**：确保 Rekordbox 绕过内部哈希或路径缓存，并正确渲染 XML 中的 Hotcues。

### C. ID 闭环映射 (ID Synchronization)
- **要求**：XML 中的 `TrackID` 必须优先继承 Rekordbox 的真实数据库 ID（若存在），否则使用高位随机 ID。

---

## 4. 结构探测决策流 (Analysis Decision Flow)

当分析引擎处理音轨时，应按照以下优先级获取结构数据：

1. **Sorter 显性计算**：如果 Sorter 已根据 Set 上下文计算了 `mix_in/out`，则强制锁定为 A/C/H 点。
2. **RB 官方 Phrase (PSSI)**：读取 `.EXT/.2EX` 文件中的乐句标签。
3. **物理扫描 Fallback**：若上述缺失，物理调用 Librosa 进行能量梯度扫描（定位 Drop E/G）。

---

## 4. 交付与验证规范 (Curation Verification)
- **文件夹偏好**：默认输出路径应为 `D:\生成的set`。
- **命名规范**：验证期音轨应添加 `✅[AI_FULL_V5.4]` 后缀以区别缓存。

---

> [!TIP]
> **制度化的力量**：当你发现标点缺失或导入失败时，请优先检查是否违反了第 2 章的盘符编码规则。
