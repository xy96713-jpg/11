import sys
from pathlib import Path
import os
import xml.etree.ElementTree as ET

# 设置路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 模拟 3 首风格连贯的小组合
test_tracks = [
    {
        'id': '1001',
        'file_path': 'D:/songs/A.mp3',
        'title': 'Vivid Dreams (Y2K Edit)',
        'artist': 'Aesthetic Producer',
        'bpm': 124.0, 'duration': 210, 'key': '1A',
        'mood': 'Euphoric', 'vibe': 'Y2K', 'energy': 75
    },
    {
        'id': '1002',
        'file_path': 'D:/songs/B.mp3',
        'title': 'Midnight City (Remix)',
        'artist': 'Neon Rider',
        'bpm': 126.0, 'duration': 180, 'key': '1A',
        'mood': 'Nostalgic', 'vibe': 'Cyberpunk', 'energy': 85
    },
    {
        'id': '1003',
        'file_path': 'D:/songs/C.mp3',
        'title': 'Digital Love (Nu-Disco)',
        'artist': 'Future Funk',
        'bpm': 125.0, 'duration': 240, 'key': '2A',
        'mood': 'Happy', 'vibe': 'Retro', 'energy': 65
    }
]

print("="*60)
print("  Intelligence-V5.3 审美标点演示 (3首迷你组合)")
print("="*60)

for track in test_tracks:
    print(f"\n🔍 正在处理: {track['title']} [{track['mood']} / {track['vibe']}]")
    try:
        # 调用 V3 标点引擎
        hcs = generate_hotcues(
            audio_file=track['file_path'],
            bpm=track['bpm'],
            duration=track['duration'],
            structure={'id': track['id']},
            content_id=track['id'], # 模拟有效 ID
            track_tags={
                'mood': track['mood'],
                'vibe': track['vibe'],
                'energy': track['energy']
            }
        )
        track['pro_hotcues'] = hcs
        
        # 打印关键点位预览
        print(f"  [标点预览]")
        cues = hcs.get('hotcues', {})
        for char in ['A', 'B', 'C', 'D', 'E', 'F']:
            cue = cues.get(f'hotcue_{char}')
            if cue:
                color_name = "未知"
                # 反查颜色名以便显示
                color_hex = cue.get('Color', '')
                if color_hex == "0x0000FF": color_name = "蓝色 (过渡)"
                elif color_hex == "0xFF0000": color_name = "红色 (能量)"
                elif color_hex == "0xFFFF00": color_name = "黄色 (氛围)"
                elif color_hex == "0x00FF00": color_name = "绿色 (混搭)"
                
                print(f"    - {char} 点: {cue['name']:<25} | 时间: {cue['seconds']:.3f}s | 颜色: {color_name}")
    except Exception as e:
        print(f"  ❌ 标点生成失败: {e}")

# 生成 XML
output_xml = Path("d:/anti/mini_set_demo.xml")
export_to_rekordbox_xml(test_tracks, output_xml, "Mini Aesthetic Set")

print("\n" + "="*60)
print(f"✅ XML 已导出至: {output_xml}")
print("="*60)
