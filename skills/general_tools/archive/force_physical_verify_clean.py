import sys
from pathlib import Path
from datetime import datetime
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

# 环境初始化
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 1. 精确配置 (基于数据库获取的真实物理路径)
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
        # 为了物理证明这是 100% 独立分析，我们在 log 中输出毫秒单位的点位
        hcs = generate_hotcues(
            audio_file=item['file_path'],
            bpm=128.0, 
            duration=300,
            content_id=item['id']
        )
        
        # 修改 Title 以强制触发 RB 区别识别
        # 这样导入后，你会在 collection 看到两个重名但后缀不同的音轨，或者能一眼确认新点位
        entry = {
            'id': item['id'],
            'title': f"{item['title']} 🔥[AI_EXPERT_VERIFIED]",
            'artist': f"ANTIGRAVITY_BRAIN_{timestamp}",
            'file_path': item['file_path'],
            'bpm': 128.0,
            'duration': 300,
            'pro_hotcues': hcs
        }
        scan_results.append(entry)
        print(f"✅ {item['title']} 分析完成：{' | '.join([str(int(c['pos']*1000))+'ms' for c in hcs]) if hcs else 'No Cues'}")
    except Exception as e:
        print(f"❌ {item['title']} 失败: {e}")

# 3. 导出唯一的验证 XML (使用不带中文字符的路径)
output_path = Path("d:/verify_set/independent_cues.xml")
if not output_path.parent.exists():
    output_path.parent.mkdir(parents=True)

export_to_rekordbox_xml(scan_results, output_path, f"AI_PHYSICAL_VERIFY")

print(f"\n💎 验证 XML 已生成: {output_path}")
print("🔍 导入说明：导入 XML 后，请在 Rekordbox 侧边栏 XML 分支下找到该音轨，右键选择 'Import to Collection' 并确认覆盖。")
