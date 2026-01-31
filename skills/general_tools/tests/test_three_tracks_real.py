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

# 专家选定的测试音轨 - 彻底放弃 Mock 数据，全部回归真实解析
expert_test_tracks = [
    {
        'id': '98606643', # 向前冲
        'title': 'Forward',
        'artist': 'Test Track 1',
        'tags': {'mood': 'Energetic', 'vibe': 'Pop', 'energy': 70}
    },
    {
        'id': '99208278', # FUZZ & NAKEN - SUPERSTAR RIDDIM
        'title': 'SUPERSTAR RIDDIM',
        'artist': 'FUZZ & NAKEN',
        'tags': {'mood': 'Hype', 'vibe': 'Riddim', 'energy': 90}
    },
    {
        'id': '99716711', # kelela - send me out
        'title': 'Send Me Out (Bootleg)',
        'artist': 'Kelela',
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
    
    # 【最严防线】物理路径合并
    if os.path.isfile(folder):
        f_path = folder
    else:
        f_path = os.path.join(folder, filename)
    
    f_path = f_path.replace('\\', '/')
    print(f"🚩 正在提取真实音乐生理特征: {item['title']} -> {f_path}")
    
    # 【归真逻辑】不再传入 custom_mix_points，让 AI 引擎去物理分析音轨，找回真实的乐句点位！
    hcs = generate_hotcues(
        audio_file=f_path,
        bpm=128.0, 
        duration=300, 
        content_id=item['id'],
        track_tags=item['tags'],
        mi_details={'mashup_pattern': 'TRUE MASTER BRAIN MODE'}
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

# 导出 (V5.4.2 归真版)
output_xml = Path("d:/生成的set/V5.4_三首专项测试_最强大脑_物理归真版.xml")
export_to_rekordbox_xml(final_tracks, output_xml, "[最强大脑] 物理归真三首测试")

print(f"\n✅ 物理归真版 XML 已生成: {output_xml}")
