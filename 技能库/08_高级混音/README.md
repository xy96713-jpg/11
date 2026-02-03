# 🎚️ 高级混音大师 (Mashup Intelligence)

> **核心功能**: 自动化混音、Mashup 制作与 Sonic DNA 音色融合。

## 1. 模块组成
- **Mashup Core**: 负责根据 Key/BPM 自动匹配两首歌的片段。
- **Sonic Worker**: 负责频谱填充与音色润色。

## 2. 使用场景
- DJSET 备场时，自动生成两首歌的过渡段 (Transition)。
- 制作 Bootleg / Edit 版本。

## 3. 脚本调用
```powershell
# 简单调用 (需传入两个音频路径)
python scripts/mashup_core.py "track_a.mp3" "track_b.mp3"
```
