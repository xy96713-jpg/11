import sys
from pathlib import Path
import os
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

# 设置路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml
from core.physical_isolator import Isolator  # 【物理隔离】导入隔离器

# 1. 从数据库中获取真实的 3 首歌
db = Rekordbox6Database()
# Rekordbox 6 字段名通常是 Title 而不是 Name
query = text("""
    SELECT ID, Title, FolderPath, BPM
    FROM djmdContent 
    WHERE FolderPath IS NOT NULL AND Title IS NOT NULL
    LIMIT 3
""")
rows = db.session.execute(query).fetchall()

test_tracks = []
for row in rows:
    test_tracks.append({
        'id': str(row[0]),
        'title': row[1],
        'artist': 'Various Artists',
        'file_path': row[2],
        'bpm': row[3] / 100.0 if row[3] else 120.0,
        'duration': 180, 
        'mood': 'VIBRANT', 'vibe': 'CLUB', 'energy': 80 
    })

print("="*80)
print("  Intelligence-V5.3 审美标点线上实机演示 (基于真实数据库)")
print("="*80)

for track in test_tracks:
    print(f"\n🎵 正在处理: {track['title']}")
    
    # 【物理隔离】执行文件复制与路径替换
    try:
        new_path = Isolator.process_track(
            file_path=track['file_path'],
            metadata={'title': track['title']}
        )
        # 更新路径，XML 将指向 D:\生成的set
        track['file_path'] = new_path
        # print(f"    [Isolation] Path updated: {new_path}")
    except Exception as e:
        print(f"    [Isolation] Failed: {e}")

    try:
        hcs = generate_hotcues(
            audio_file=track['file_path'],
            bpm=track['bpm'],
            duration=track['duration'],
            content_id=track['id'],
            track_tags={
                'mood': track['mood'],
                'vibe': track['vibe'],
                'energy': track['energy']
            }
        )
        track['pro_hotcues'] = hcs
        
        # 详细打印 cues
        cues = hcs.get('hotcues', {})
        if not cues:
            print("    ⚠️ 该歌曲暂无 PQTZ 节拍网格数据，回退至基础逻辑。")
        else:
            # 兼容 V6.0 标准 (A, B, C, D, E) 和 V3 标准 (hotcue_A)
            keys = ['A', 'B', 'C', 'D', 'E']
            for char in keys:
                cue = cues.get(char) or cues.get(f'hotcue_{char}')
                if cue:
                    color_name = "未知"
                    color_hex = cue.get('Color', '') or cue.get('color', '')
                    if color_hex == "0x0000FF": color_name = "🔵 蓝色 (过渡)"
                    elif color_hex == "0xFF0000": color_name = "🔴 红色 (能量)"
                    elif color_hex == "0xFFFF00": color_name = "🟡 黄色 (平稳)"
                    elif color_hex == "0x00FF00": color_name = "🟢 绿色 (创意)"
                    elif color_hex == "0x00FFFF": color_name = "🔵 青色 (桥接)"
                    
                    name = cue.get('Name') or cue.get('name')
                    start = float(cue.get('Start') or cue.get('time') or cue.get('seconds') or 0)
                    print(f"    [{char}] {name:<25} | {start:>7.3f}s | {color_name}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

output_xml = Path("d:/生成的set/mini_set_real.xml")
export_to_rekordbox_xml(test_tracks, output_xml, "Real Aesthetic Set")

print("\n" + "="*80)
print(f"✅ XML 已导出至: {output_xml}")
print("="*80)
