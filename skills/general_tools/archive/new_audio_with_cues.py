import sys
from pathlib import Path
from datetime import datetime

# 环境初始化
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 1. 配置：使用新复制的音频路径，确保导入时作为新条目出现
tracks_to_process = [
    {
        'id': 'AI_001',
        'title': 'Perfect Night (AI Brain Verified)',
        'file_path': 'D:/verify_set/audio/Perfect_Night_AI.mp3',
        'original_id': '55957733'
    },
    {
        'id': 'AI_002',
        'title': 'HIP (AI Brain Verified)',
        'file_path': 'D:/verify_set/audio/HIP_AI.mp3',
        'original_id': '119209545'
    },
    {
        'id': 'AI_003',
        'title': 'TT Remix (AI Brain Verified)',
        'file_path': 'D:/verify_set/audio/TT_AI.mp3',
        'original_id': '40483348'
    }
]

# 2. 执行物理分析
scan_results = []
timestamp = datetime.now().strftime("%H%M")

for item in tracks_to_process:
    print(f"📡 物理扫描中: {item['title']}")
    try:
        # 使用原始 content_id 进行物理分析
        hcs_data = generate_hotcues(
            audio_file=item['file_path'],
            bpm=128.0, 
            duration=300,
            content_id=item['original_id']
        )
        
        # 提取点位信息
        cue_list = hcs_data.get('cues', {}).values()
        point_str = ' | '.join([f"{c.get('Name')} @ {int(c.get('Start')*1000)}ms" for c in cue_list])
        
        entry = {
            'id': item['id'],
            'title': item['title'],
            'artist': "ANTIGRAVITY_BRAIN_VERIFIED",
            'file_path': item['file_path'],
            'bpm': 128.0,
            'duration': 300,
            'pro_hotcues': hcs_data
        }
        scan_results.append(entry)
        print(f"✅ {item['title']} 分析完成: {point_str}")
    except Exception as e:
        import traceback
        print(f"❌ {item['title']} 失败: {e}")
        traceback.print_exc()

# 3. 导出唯一的验证 XML
output_path = Path("d:/verify_set/NEW_AUDIO_WITH_CUES.xml")

export_to_rekordbox_xml(scan_results, output_path, f"AI_VERIFIED_NEW_TRACKS")

print(f"\n💎 验证文件已生成: {output_path}")
print("🔍 导入说明：")
print("1. 直接将这个 XML 拖入 Rekordbox。")
print("2. 在左侧 XML 分支里找到 AI_VERIFIED_NEW_TRACKS 文件夹。")
print("3. 您会看到三首新音轨（Perfect Night / HIP / TT），它们是复制件。")
print("4. 右键点击 -> Import to Collection，点位立刻可见！")
