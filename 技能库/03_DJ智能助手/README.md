# 🎧 DJ 智能助手 (DJ Intelligence / Master DJ V4.0 Ultra+)

本模块是专为现场演奏与曲库管理设计的“双系统”专家引擎。它不仅能处理单曲，更能以全局视野重构您的现场能量流。

## 🌟 双核心系统 (The Dual System)

### 系统 A：Mashup 和谐度智能推荐 (Mashup Recommender)
- **底层资产**: `assets/mashup_recommender.py`, `assets/find_ninja_mashup.py` 等。
- **核心逻辑**: 
  - **谐波锁定 (Key Locking)**：自动计算两首歌在 Camelot Wheel 上的兼容性点数。
  - **人声冲突审计**：前置识别 Vocal 与 Lead Synth 的频率重叠风险。
  - **相位对齐建议**：提供精准的切入点（In/Out Point）小节数建议。

### 系统 B：Narrative 能量流排 Set 系统 (Set Curator)
- **底层资产**: `assets/narrative_set_planner.py`, `assets/enhanced_harmonic_set_sorter.py` 等。
- **核心逻辑**:
  - **能量梯阶 (Energy Gradient)**：基于轨迹能量值自动排布“开场-铺垫-爆发-收尾”的审美曲线。
  - **BPM 顺滑化**：自动规划 BPM 阶梯增长路经，杜绝突兀的跳速感。
  - **乐句对齐排列**：所有曲目排列均符合 32 小节乐句（Phrasing）呼吸感。

---

## 📖 用户操作指南 (User Manual)

### 1. 想要查询 Mashup 可能性？
您可以直接问我两个曲目的配合度：
- **示例**：`“帮我看看 [A歌曲] 和 [B歌曲] 适合 Mashup 吗？”`
- **示例**：`“在我的库里给这首 [NewJeans - Ditto] 找几个完美的 Harmonic Match”`

### 2. 想要自动排出一场完整的 Set？
您可以要求我策划一个具有叙事感的曲目单：
- **示例**：`“帮我策划一个 1 小时的 Deep House Set，能量值从 3 逐步升高到 8”`
- **示例**：`“优化一下我当前的这个清单顺序，让过门更自然”`

---

## 🤖 AI 激活指令 (Agent Activation)

若需 AI 进入 Master DJ 模式，请使用以下专业词汇：

- **“启动 Master DJ 双系统逻辑，针对...”**
- **“调用 Mashup 推荐引擎评估...”**
- **“执行 Narrative 排 Set 算法，目标时长...”**
- **“执行乐句对齐与相位一致性审计”**

> **AI 行为逻辑**：Agent 会调用 `assets/` 中的 `enhanced_harmonic_set_sorter.py`，并结合 `GEMINI.md` 中的音频工程红线（Gain Staging / Zero-Crossing）进行决策。

---

## 🛠️ 技术存档 (Tech Specs)
- **版本**: V4.0 Ultra+ (Full Dual System)
- **更新时间**: 2026-01-31
- **资产池**: `assets/` 文件夹下共有 49 个核心驱动与 95 个辅助脚本，支持全自动 Rekordbox XML 数据库交互。

---
> [!IMPORTANT]
> **本模块不仅是工具，更是您的审美分身。** 所有建议均基于专业 DJ 乐理，而非单纯的数学对齐。
