import sys
from pathlib import Path
import os
import bisect

# 模拟路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
try:
    from skills.cueing_intelligence.scripts.v3 import generate_intelligent_cues_v3, COLORS
except ImportError:
    # Fallback for older path if new path fails
    from skills.skill_hotcue_intelligence_v3 import generate_intelligent_cues_v3, COLORS

# 1. 模拟底层分析数据 (PQTZ + PSSI)
mock_beat_times = [i * 0.5 for i in range(1000)] # 120 BPM, 每 0.5s 一拍
mock_phrases = [
    {'beat': 1, 'kind': 1},   # Intro
    {'beat': 33, 'kind': 2},  # Verse 1 (B点)
    {'beat': 129, 'kind': 3}, # Chorus/Drop (E点)
    {'beat': 257, 'kind': 10} # Outro (C点)
]

def mock_get_analysis(cid):
    return {
        'bpm': 120.0,
        'beat_times': mock_beat_times,
        'phrases': mock_phrases
    }

# 猴子补丁，绕过数据库连接
import skills.skill_hotcue_intelligence_v3
skills.skill_hotcue_intelligence_v3.get_rekordbox_analysis = mock_get_analysis

print("="*80)
print("  Intelligence-V5.3 审美标点引擎 - 逻辑演示报告")
print("="*80)

# 2. 测试不同情绪和能量的标记效果
test_cases = [
    {'name': 'Euphoric Pop', 'mood': 'Happy', 'vibe': 'Sunny', 'energy': 60},
    {'name': 'Dark Techno', 'mood': 'Dark', 'vibe': 'Hard', 'energy': 95},
    {'name': 'Chill R&B', 'mood': 'Relaxed', 'vibe': 'Smooth', 'energy': 30}
]

for case in test_cases:
    print(f"\n🎵 模拟曲目: {case['name']} (能量: {case['energy']})")
    
    result = generate_intelligent_cues_v3(
        content_id="mock_id",
        duration=300,
        track_tags=case,
        mi_details={'mashup_pattern': 'Vocals (A) + Instrumental (B)', 'bass': 'No Conflict'}
    )
    
    cues = result['cues']
    print(f"   [Hotcue A-H 布局]")
    for char in ['A', 'B', 'C', 'D', 'E', 'F']:
        if char in cues:
            data = cues[char]
            # 颜色翻译
            color_name = "WHITE"
            for name, val in COLORS.items():
                if val == data['Color']: color_name = name
            
            print(f"    - [{char}] {data['Name']:<25} | {data['Start']:>5.1f}s | 🎨 {color_name}")
            
    print(f"   [Memory Cues 提示库]")
    for m in result['memory_cues']:
        print(f"    - 📝 {m['Name']} at {m['Start']}s")

print("\n" + "="*80)
print("✅ 演示完成：系统已根据情绪标签（Mood/Vibe）自动调整命名与颜色分级。")
print("="*80)
