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

# 1. 直接从数据库提取带有物理路径的音频文件
db = Rekordbox6Database()

# 使用 FileNameL (Long FileName) 字段确保路径完整性
query = text("""
    SELECT ID, Title, BPM, FolderPath, FileNameL
    FROM djmdContent 
    WHERE FolderPath IS NOT NULL AND FolderPath != ''
    LIMIT 3
""")
rows = db.session.execute(query).fetchall()

test_tracks = []
for row in rows:
    cid = row[0]
    title = row[1]
    bpm_raw = row[2]
    folder = row[3]
    filename = row[4] # FileNameL
    
    # 物理路径拼接 (Windows)
    f_path = os.path.join(folder, filename).replace('\\', '/')
    
    test_tracks.append({
        'id': str(cid),
        'title': title,
        'artist': 'Expert Rule Core',
        'file_path': f_path,
        'bpm': (bpm_raw or 12000) / 100.0,
        'duration': 180, 
        'mood': 'VIBRANT', 'vibe': 'CLUB', 'energy': 80 
    })

print(f"🚩 正在生成专家规则库 (AB进/CD出)... (音轨数: {len(test_tracks)})")

for track in test_tracks:
    print(f"  🔍 处理: {track['title']} -> {track['file_path']}")
    try:
        # 调用标点引擎
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
        
        # 调试输出
        cues = hcs.get('cues', {})
        print(f"    ✅ 成功映射 {len(cues)} 个标点: {list(cues.keys())}")
        
    except Exception as e:
        print(f"    ❌ 失败: {e}")

# 生成 XML
output_dir = Path("d:/生成的set")
output_dir.mkdir(parents=True, exist_ok=True)
output_xml = output_dir / "V5.3_核心专家规则_物理对齐版.xml"

export_to_rekordbox_xml(test_tracks, output_xml, "[核心专家] AB进CD出")

print(f"\n✅ 成功！演示文件已生成: {output_xml}")
print("---")
print("规则说明：")
print("1. A/B 负责进歌窗 (蓝色/黄色)")
print("2. C/D 负责出歌窗 (蓝色/蓝色)")
print("3. Location 已修复，驱动器号后必带 /")
