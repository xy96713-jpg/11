import sys
from pathlib import Path
from datetime import datetime
import os

# 环境初始化
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 1. 精确配置
tracks_to_process = [
    {
        'id': '55957733',
        'title': 'LE SSERAFIM Perfect Night (NΣΣT Remix)',
        'file_path': 'D:/song/kpop house/LE SSERAFIM Perfect Night (NΣΣT Remix).mp3'
    },
    {
        'id': '119209545',
        'title': 'MAMAMOO - HIP(JXXXXX edit)',
        'file_path': 'D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3'
    },
    {
        'id': '40483348',
        'title': 'Twice - Tt (Visrah X Noguchii Remix)',
        'file_path': 'D:/song/kpop house/Twice - Tt (Visrah X Noguchii Remix).mp3'
    }
]

# 2. 执行物理分析
scan_results = []
timestamp = datetime.now().strftime("%H%M")

for item in tracks_to_process:
    print(f"📡 物理扫描中: {item['title']}")
    try:
        # hcs format: {'cues': {'A': {...}, ...}, 'memory_cues': [], ...}
        hcs_data = generate_hotcues(
            audio_file=item['file_path'],
            bpm=128.0, 
            duration=300,
            content_id=item['id']
        )
        
        # 修复 Print 逻辑：提取字典中的 Start 点位
        cue_list = hcs_data.get('cues', {}).values()
        point_str = ' | '.join([f"{c.get('Name')} @ {int(c.get('Start')*1000)}ms" for c in cue_list])
        
        # 修改 Title 以强制触发 RB 区别识别
        entry = {
            'id': item['id'],
            'title': f"{item['title']} ✅[AI_BRAIN_V2]",
            'artist': f"VERIFIED_BY_ANTIGRAVITY",
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
output_path = Path("d:/verify_set/final_expert_verify.xml")
if not output_path.parent.exists():
    output_path.parent.mkdir(parents=True)

export_to_rekordbox_xml(scan_results, output_path, f"EXPERT_CURATION_VERIFY")

print(f"\n💎 验证 XML 已生成: {output_path}")
print("🔍 导入说明：")
print("1. 在 Rekordbox 侧边栏找到 XML -> 刷新 -> AI_PHYSICAL_VERIFY 文件夹。")
print("2. 找到带有 ✅[AI_BRAIN_V2] 后缀的这三首歌。")
print("3. 右键点击音轨 -> Import to Collection（导入到集合）。")
print("4. 如果提示文件已存在，请确认覆盖，重点看 Artist 是否变成了 VERIFIED_BY_ANTIGRAVITY。")
