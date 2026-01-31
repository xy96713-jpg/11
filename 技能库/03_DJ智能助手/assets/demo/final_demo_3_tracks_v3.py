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

# 使用非常通用的查询
query = text("""
    SELECT ID, Title, BPM
    FROM djmdContent 
    LIMIT 3
""")
rows = db.session.execute(query).fetchall()

# 我们需要手动获取路径，因为不同版本的字段名不同
test_tracks = []
for row in rows:
    # 获取完整的 Content 记录以探索字段
    cid = row[0]
    full_row = db.session.execute(text(f"SELECT * FROM djmdContent WHERE ID = '{cid}'")).fetchone()
    
    # 尝试找到路径
    f_path = ""
    # row._mapping is available in SQLAlchemy 1.4+
    m = full_row._mapping
    if 'Path' in m: f_path = m['Path']
    elif 'FilePath' in m: f_path = m['FilePath']
    elif 'FolderPath' in m and 'FileName' in m:
        f_path = os.path.join(m['FolderPath'], m['FileName'])
    
    test_tracks.append({
        'id': str(cid),
        'title': m.get('Title', 'Unknown'),
        'artist': 'Aesthetic Demo',
        'file_path': f_path,
        'bpm': m.get('BPM', 12000) / 100.0,
        'duration': 180, 
        'mood': 'VIBRANT', 'vibe': 'CLUB', 'energy': 80 
    })

print(f"选中了 {len(test_tracks)} 首歌进行标点...")

for track in test_tracks:
    print(f"  - {track['title']} (ID: {track['id']})")
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
    except Exception as e:
        print(f"    ❌ 失败: {e}")

# 清空目录并生成唯一的 XML
output_dir = Path("d:/生成的set")
if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)
else:
    # 只清理本演示相关文件
    for f in output_dir.glob("*审美演示*"):
        f.unlink()

output_xml = output_dir / "V5.3_顶级审美标点_仅3首.xml"
export_to_rekordbox_xml(test_tracks, output_xml, "[演示] 3首标点展示")

print(f"\n✅ 成功！已生成唯一的演示文件: {output_xml}")
