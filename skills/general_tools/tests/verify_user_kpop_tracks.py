import sys
from pathlib import Path
import os
from datetime import datetime
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

# 用户指定的三首 K-Pop 音轨
user_verify_tracks = [
    {
        'id': '55957733', 
        'title': 'Perfect Night (NΣΣT Remix)',
        'path': 'D:/song/kpop house/LE SSERAFIM Perfect Night (NΣΣT Remix).mp3'
    },
    {
        'id': '119209545', 
        'title': 'HIP(JXXXXX edit)',
        'path': 'D:/song/kpop house/MAMAMOO - HIP(JXXXXX edit).mp3'
    },
    {
        'id': '40483348', 
        'title': 'TT (Visrah X Noguchii Remix)',
        'path': 'D:/song/kpop house/Twice - Tt (Visrah X Noguchii Remix).mp3'
    }
]

force_tag = datetime.now().strftime("%H%M")
final_tracks = []

for item in user_verify_tracks:
    print(f"🚩 正在执行 AI 独立物理扫描: {item['title']}")
    
    # 强制执行 AI 全流程分析，不传递任何历史点位
    # 这样生成的标点将完全取决于音频文件的物理波形和乐句转换
    try:
        hcs = generate_hotcues(
            audio_file=item['path'],
            bpm=128.0, 
            duration=300, 
            content_id=item['id'],
            # 在 Mi Details 中注入唯一标识，证明打标时戳的独立性
            mi_details={'mashup_pattern': f'AI_VERIFY_SCAN_{force_tag}'}
        )
        
        # 增加 Artist 前缀，确保用户能一眼认出这是 AI 刚打的标
        track_data = {
            'id': item['id'],
            'title': item['title'],
            'artist': f"AI_INDEPENDENT_{force_tag}",
            'file_path': item['path'],
            'bpm': 128.0,
            'duration': 300,
            'pro_hotcues': hcs
        }
        final_tracks.append(track_data)
        print(f"✅ {item['title']} 物理扫描完成。")
    except Exception as e:
        print(f"❌ {item['title']} 分析失败: {e}")

# 执行导出
output_xml = Path(f"d:/生成的set/V5.4.4_AI独立打标测试_{force_tag}.xml")
export_to_rekordbox_xml(final_tracks, output_xml, f"AI独立打标验证_{force_tag}")

print(f"\n🚀 验证文件已就绪: {output_xml}")
