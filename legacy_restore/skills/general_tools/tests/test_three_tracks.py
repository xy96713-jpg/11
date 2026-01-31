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

# 专家选定的测试音轨
expert_test_tracks = [
    {
        'id': '98606643', # 向前冲
        'title': 'Forward',
        'artist': 'Test Track 1',
        'mix_in': 0.0,
        'transition_in': 30.0,
        'mix_out': 180.0,
        'tags': {'mood': 'Energetic', 'vibe': 'Pop', 'energy': 70}
    },
    {
        'id': '99208278', # FUZZ & NAKEN - SUPERSTAR RIDDIM
        'title': 'SUPERSTAR RIDDIM',
        'artist': 'FUZZ & NAKEN',
        'mix_in': 1.0,
        'transition_in': 15.5,
        'mix_out': 210.0,
        'tags': {'mood': 'Hype', 'vibe': 'Riddim', 'energy': 90}
    },
    {
        'id': '99716711', # kelela - send me out
        'title': 'Send Me Out (Bootleg)',
        'artist': 'Kelela',
        'mix_in': 5.0,
        'transition_in': 45.0,
        'mix_out': 255.0,
        'tags': {'mood': 'Deep', 'vibe': 'Electronic', 'energy': 50}
    }
]

db = Rekordbox6Database()
final_tracks = []

for item in expert_test_tracks:
    query = text("SELECT FolderPath, FileNameL FROM djmdContent WHERE ID = :cid")
    row = db.session.execute(query, {"cid": item['id']}).fetchone()
    if not row: continue
    
    folder = row[0]
    filename = row[1]
    
    if os.path.isfile(folder):
        f_path = folder
    else:
        f_path = os.path.join(folder, filename)
    
    f_path = f_path.replace('\\', '/')
    print(f"🚩 正在处理测试音轨: {item['title']} -> {f_path}")
    
    # 调用标点引擎
    hcs = generate_hotcues(
        audio_file=f_path,
        bpm=128.0, # 模拟值
        duration=300, # 模拟值
        content_id=item['id'],
        track_tags=item['tags'],
        custom_mix_points={
            'mix_in': item['mix_in'],
            'transition_in': item['transition_in'],
            'mix_out': item['mix_out']
        },
        mi_details={'mashup_pattern': 'AI Expert Test Mode'}
    )
    
    track_data = {
        'id': item['id'],
        'title': item['title'],
        'artist': item['artist'],
        'file_path': f_path,
        'bpm': 128.0,
        'duration': 300,
        'pro_hotcues': hcs
    }
    final_tracks.append(track_data)

# 导出
output_xml = Path("d:/生成的set/V5.4_三首专项测试_最强大脑.xml")
export_to_rekordbox_xml(final_tracks, output_xml, "[最强大脑] 三首专项测试")

print(f"\n✅ 专项测试 XML 已生成: {output_xml}")
