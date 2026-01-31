import sys
from pathlib import Path

# 设置环境路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "skills"))

from enhanced_harmonic_set_sorter import _calculate_candidate_score, MASHUP_ENABLED
from auto_hotcue_generator import generate_hotcues
import json

def test_integration():
    print("--- [V7 集成验证] ---")
    print(f"MI 引擎状态: {'ENABLED' if MASHUP_ENABLED else 'DISABLED'}")
    
    # 负载模拟数据 (两个差异性大的轨道)
    track1 = {
        'id': 'T1',
        'title': 'Vocal House A',
        'bpm': 124.0,
        'key': '1A',
        'energy': 60,
        'vocal_ratio': 0.8, # 极高人声
        'kick_drum_power': 0.3, # 弱底鼓
        'spectral_bands': {'mid_range': 0.8, 'high_presence': 0.7}
    }
    
    track2 = {
        'id': 'T2',
        'title': 'Deep Tech B',
        'bpm': 125.0,
        'key': '1A',
        'energy': 65,
        'vocal_ratio': 0.2, # 极低人声
        'kick_drum_power': 0.9, # 强底鼓
        'spectral_bands': {'mid_range': 0.2, 'high_presence': 0.3}
    }
    
    # 模拟 Sorter 评分数据
    track_data = (track2, track1, 124.0, 50, 75, "Peak", [], False)
    
    print("\n[1] 验证 Sorter 评分注入...")
    score, track_res, metrics = _calculate_candidate_score(track_data)
    
    print(f"总得分: {score:.1f}")
    if 'mi_score' in metrics:
        print(f"MI 得分: {metrics['mi_score']:.1f}")
        print(f"MI 细节: {metrics['mi_details']}")
    else:
        print("错误: metrics 中缺失 mi_score")

    print("\n[2] 验证智能 Memory Cues 路由...")
    # 模拟 Sorter 到 Generator 的透传
    mi_details = metrics.get('mi_details', {})
    
    # 检查 B 点生成的指令
    cues = generate_hotcues(
        audio_file="dummy.mp3",
        bpm=125.0,
        duration=180,
        structure=track2,
        vocal_regions=[],
        mi_details=mi_details,
        id='T2' # 触发 V2 引擎
    )
    
    found_stems_instruction = False
    found_bass_instruction = False
    
    print("生成的 Memory Cues:")
    for mc in cues.get('memory_cues', []):
        name = mc.get('Name') or mc.get('name') or mc.get('comment')
        print(f"  - {name}")
        if name and "MASHUP:" in name: found_stems_instruction = True
        if name and "BASS CLASH: CUT EQ" in name: found_bass_instruction = True
        
    if found_stems_instruction:
        print("\n✅ 验证成功: Stems 互补指令已生成")
    else:
        print("\n❌ 验证失败: 未找到 Stems 指令")

if __name__ == "__main__":
    test_integration()
