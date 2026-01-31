import os
import sys
from pathlib import Path

# 确保导入路径正确
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_harmonic_set_sorter import enhanced_harmonic_sort, generate_hotcues
from exporters.xml_exporter import export_to_rekordbox_xml

def test_8_tracks_consistency():
    # 查找测试音轨 (使用 D:\ 根目录下的 MP3)
    audio_files = list(Path("D:/").glob("*.mp3"))[:8]
    if len(audio_files) < 2:
        print("错误：D盘根目录下 mp3 文件不足，请确保至少有 2 首用于测试。")
        return

    tracks = []
    for f in audio_files:
        # 简单模拟音轨数据
        tracks.append({
            'file_path': str(f),
            'title': f.stem,
            'artist': 'Test Artist',
            'bpm': 128.0,
            'key': '1A',
            'energy': 50,
            'duration': 180,
            'id': f.stem.replace(' ', '_')
        })

    print(f"正在对 {len(tracks)} 首音轨执行最强大脑排序...")
    # 执行排序 (这会生成混音建议逻辑)
    # 注意：在真实的 sorter 中，它是由一组复杂的循环完成的。
    # 这里我们直接运行一部分核心逻辑
    sorted_set = enhanced_harmonic_sort(tracks, target_count=8, is_boutique=True)
    
    # 手动触发标记逻辑
    for i, track in enumerate(sorted_set):
        # 检查 mix_in_point 和 mix_out_point 是否被更新
        print(f"Track: {track['title']} | Mix-In: {track.get('mix_in_point')} | Mix-Out: {track.get('mix_out_point')}")

if __name__ == "__main__":
    test_8_tracks_consistency()
