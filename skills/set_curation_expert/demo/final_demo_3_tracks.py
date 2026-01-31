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

# 1. 从数据库中获取真实的 3 首歌
db = Rekordbox6Database()
# Rekordbox 6
query = text("""
    SELECT ID, Title, Path, BPM
    FROM djmdContent 
    WHERE Path LIKE 'D:/song/Boiler Room/%'
    LIMIT 3
""")
rows = db.session.execute(query).fetchall()

test_tracks = []
for row in rows:
    test_tracks.append({
        'id': str(row[0]),
        'title': row[1],
        'artist': 'Aesthetic Demo',
        'file_path': row[2],
        'bpm': row[3] / 100.0 if row[3] else 120.0,
        'duration': 180, 
        'mood': 'VIBRANT', 'vibe': 'CLUB', 'energy': 80 
    })

print(f"选中了 {len(test_tracks)} 首歌进行标点...")

for track in test_tracks:
    print(f"  - {track['title']}")
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

# 清空目录并生成唯一的 XML
output_dir = Path("d:/生成的set")
if output_dir.exists():
    import shutil
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_xml = output_dir / "V5.3_审美标点演示_仅3首.xml"
export_to_rekordbox_xml(test_tracks, output_xml, "[演示] 审美感知标点")

print(f"\n✅ 成功！已生成唯一的演示文件: {output_xml}")
