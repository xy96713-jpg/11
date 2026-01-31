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

# 选定的三首全新测试音轨
expert_test_tracks = [
    {'id': '209478487', 'title': 'Kore'},
    {'id': '102001189', 'title': 'Stay With Me'},
    {'id': '243180728', 'title': 'Paranoia'}
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
    print(f"🚩 正在提取真实音乐生理特征: {item['title']} -> {f_path}")
    
    # 物理归真分析：基于真实的乐句结构
    try:
        hcs = generate_hotcues(
            audio_file=f_path,
            bpm=128.0, 
            duration=300, 
            content_id=item['id'],
            mi_details={'mashup_pattern': 'TRUE MASTER BRAIN MODE V2'}
        )
        
        track_data = {
            'id': item['id'],
            'title': item['title'],
            'artist': 'Expert AI Test',
            'file_path': f_path,
            'bpm': 128.0,
            'duration': 300,
            'pro_hotcues': hcs
        }
        final_tracks.append(track_data)
    except Exception as e:
        print(f"Error analyzing {item['title']}: {e}")

# 导出
output_xml = Path("d:/生成的set/V5.4.3_新三首_物理归真版.xml")
export_to_rekordbox_xml(final_tracks, output_xml, "[最强大脑] 新三首物理归真测试")

print(f"\n✅ 新三首 XML 已生成: {output_xml}")
