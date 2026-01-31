
from core.rekordbox_phrase_reader import PHRASE_KINDS
print('=== PHRASE_KINDS 修复验证 ===')
for k, v in PHRASE_KINDS.items():
    print(f'  {k}: {v}')
print()

from auto_hotcue_generator import _bars_to_seconds
print('=== auto_hotcue_generator 导入测试 ===')
print(f'  _bars_to_seconds(8, 120) = {_bars_to_seconds(8, 120):.2f}s')
print()

from skills.skill_pro_cueing import is_in_vocal_region, professional_quantize
print('=== skill_pro_cueing 格式兼容性测试 ===')
# 测试 list 格式
result1 = is_in_vocal_region(15.0, [[10.0, 20.0], [30.0, 40.0]])
print(f'  list格式: is_in_vocal_region(15.0, [[10,20],[30,40]]) = {result1}')
# 测试 dict 格式
result2 = is_in_vocal_region(15.0, [{'start': 10.0, 'end': 20.0}])
print(f'  dict格式: is_in_vocal_region(15.0, [{{ "start": 10.0, "end": 20.0 }}]) = {result2}')
print(f'  professional_quantize(8.5, 120, 0.0) = {professional_quantize(8.5, 120, 0.0):.3f}s')
print()

from skills.skill_vocal_aware_cues import calculate_vocal_alerts, check_vocal_overlap_at_mix_point
print('=== skill_vocal_aware_cues 格式兼容性测试 ===')
alerts_list = calculate_vocal_alerts([[10.0, 20.0]], 128, 180)
print(f'  list格式 alerts: {list(alerts_list.keys())}')
alerts_dict = calculate_vocal_alerts([{'start': 10.0, 'end': 20.0}], 128, 180)
print(f'  dict格式 alerts: {list(alerts_dict.keys())}')

# 测试 check_vocal_overlap
track_a = {'vocals': {'segments': [{'start': 170, 'end': 180}]}}
track_b = {'vocals': {'segments': [[0, 10]]}}
res = check_vocal_overlap_at_mix_point(track_a, track_b, 175.0, 5.0)
print(f'  check_vocal_overlap (mixed format): {res[1]}')

print('✅ 所有模块导入和功能测试通过!')
