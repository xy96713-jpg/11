import sys
from pathlib import Path
import os

# 环境初始化
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "exporters"))

from auto_hotcue_generator import generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

# 模拟一个 Set 序列
# Track 1 -> Track 2 (Perfect Night -> HIP)
tracks = [
    {
        'id': '55957733',
        'title': 'LE SSERAFIM Perfect Night (NΣΣT Remix)',
        'file_path': 'D:/verify_set/audio/Perfect_Night_AI.mp3',
        'bpm': 128.0,
        'genre': 'K-Pop House'
    },
    {
        'id': '119209545',
        'title': 'MAMAMOO - HIP(JXXXXX edit)',
        'file_path': 'D:/verify_set/audio/HIP_AI.mp3',
        'bpm': 128.0,
        'genre': 'K-Pop House'
    }
]

# 模拟 Sorter 的导出循环
final_results = []

for i, track in enumerate(tracks):
    print(f"📡 正在计算连通性标点: {track['title']}")
    
    # 【核心逻辑模拟】构造 Link Data
    link_data = None
    if i < len(tracks) - 1:
        next_track = tracks[i+1]
        link_data = {
            'next_title': next_track['title'],
            'next_intro_beats': 32 # 假设下一首有 32 拍 Intro
        }
    
    # 调用升级后的生成器
    hcs_data = generate_hotcues(
        audio_file=track['file_path'],
        bpm=track['bpm'],
        duration=300,
        content_id=track['id'],
        link_data=link_data, # 传递连通性负载
        track_tags={'mood': 'Energetic', 'vibe': 'Club'}
    )
    
    # 封装
    track_entry = track.copy()
    track_entry['title'] = f"{track['title']} ✨[AI_LINK_V5.4]"
    track_entry['artist'] = "AI_LINK_EXPERT"
    track_entry['pro_hotcues'] = hcs_data
    
    # 打印 H 点作为验证
    h_point = hcs_data.get('cues', {}).get('H')
    if h_point:
        print(f"   🔗 已生成连通点 H: {h_point['Name']} @ {int(h_point['Start']*1000)}ms")
    
    final_results.append(track_entry)

# 导出
output_path = Path("d:/verify_set/LINK_POINT_VERIFY.xml")
export_to_rekordbox_xml(final_results, output_path, "AI_LINK_PROTO")

print(f"\n💎 连通性测试文件已生成: {output_path}")
print("🔍 验证点：查看 Perfect Night 的 HotCue H，它应该标记了连向 HIP 的最佳切出点。")
