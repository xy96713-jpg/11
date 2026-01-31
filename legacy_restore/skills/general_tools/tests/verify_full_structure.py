import sys
from pathlib import Path
import os
import shutil

# 环境初始化
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 验证目录 (回归用户预设路径)
VERIFY_DIR = Path("D:/生成的set/")
AUDIO_DIR = VERIFY_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 目标测试曲目
source_tracks = [
    {
        'id': '55957733',
        'title': 'Perfect Night (Full Brain)',
        'src': 'D:/song/kpop house/LE SSERAFIM Perfect Night (NΣΣT Remix).mp3',
        'dst': str(AUDIO_DIR / 'Perfect_Night_Full.mp3'),
        'bpm': 128.0
    },
    {
        'id': '119209545',
        'title': 'HIP (Full Brain)',
        'src': 'D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3',
        'dst': str(AUDIO_DIR / 'HIP_Full.mp3'),
        'bpm': 128.0
    }
]

final_results = []

# 物理复制 + 标点生成
for i, track in enumerate(source_tracks):
    print(f"🚀 正在处理: {track['title']}")
    if os.path.exists(track['src']):
        shutil.copy(track['src'], track['dst'])
    
    # 构建 Link Data (下一曲的引导)
    link_data = None
    if i < len(source_tracks) - 1:
        next_track = source_tracks[i+1]
        link_data = {
            'next_title': next_track['title'],
            'next_intro_beats': 32
        }

    # 调用具备“最强大脑”内核的生成器
    hcs_data = generate_hotcues(
        audio_file=track['dst'],
        bpm=track['bpm'],
        duration=300,
        content_id=track['id'],
        link_data=link_data, 
        track_tags={'mood': 'Club', 'vibe': 'Neon', 'energy': 85}
    )
    
    # 封装输出结构
    entry = {
        'id': track['id'],
        'title': f"{track['title']} ✅[AI_FULL_V5.4]",
        'artist': "ANTIGRAVITY_BRAIN",
        'file_path': track['dst'],
        'bpm': track['bpm'],
        'pro_hotcues': hcs_data
    }
    
    # 打印点位自检
    cues = hcs_data.get('cues', {})
    points = [f"{k}:{v['Name']}" for k,v in cues.items()]
    print(f"   📍 生成点位: {' | '.join(points)}")
    
    final_results.append(entry)

# 导出唯一的物理验证 XML
xml_path = VERIFY_DIR / "FULL_STRUCTURE_CUES.xml"
export_to_rekordbox_xml(final_results, xml_path, "AI_FULL_STRUCTURE_READY")

print(f"\n💎 终极回归测试完成！")
print(f"XML 路径: {xml_path}")
print(f"验证说明：导入后请观察是否存在 E(DROP)、F(DROP2) 或 G(BRIDGE) 点位。")
