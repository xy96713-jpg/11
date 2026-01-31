import sys
from pathlib import Path
import os

# 设置路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 模拟一个 track
test_track = {
    'file_path': 'D:/songs/test.mp3',
    'title': 'Test Song',
    'artist': 'Test Artist',
    'bpm': 124.0,
    'duration': 200,
    'key': '1A',
    'structure': {'id': 1}, # 假设数据库中有 ID=1 的歌
    'mood': 'Happy',
    'vibe': 'Chill',
    'energy': 60
}

print("1. 正在尝试生成 Hotcues...")
try:
    # 模拟一个真实的 content_id (如果数据库里有)
    # 或者我们只是测试 V3 逻辑
    hcs = generate_hotcues(
        audio_file=test_track['file_path'],
        bpm=test_track['bpm'],
        duration=test_track['duration'],
        structure=test_track['structure'],
        track_tags={
            'mood': test_track['mood'],
            'vibe': test_track['vibe'],
            'energy': test_track['energy']
        }
    )
    test_track['pro_hotcues'] = hcs
    print(f"✓ Hotcues 生成成功: {hcs.keys()}")
except Exception as e:
    print(f"❌ Hotcues 生成失败: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 正在尝试生成 XML...")
try:
    output_xml = Path("d:/anti/debug_test.xml")
    export_to_rekordbox_xml([test_track], output_xml, "Debug Set")
    print(f"✓ XML 导出成功: {output_xml}")
except Exception as e:
    print(f"❌ XML 导出失败: {e}")
    import traceback
    traceback.print_exc()

if Path("d:/anti/debug_test.xml").exists():
    print("\n3. 检查 XML 内容:")
    with open("d:/anti/debug_test.xml", "r", encoding="utf-8") as f:
        print(f.read()[:500])
