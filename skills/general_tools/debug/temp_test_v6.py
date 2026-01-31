#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 V6.0 标点生成器"""

from auto_hotcue_generator import _generate_from_rekordbox_phrases

# 测试 hearts2hearts flip
result = _generate_from_rekordbox_phrases(
    content_uuid='fcb46903-42a0-4b86-8904-41920b7cc6a8',
    bpm=128.0,
    duration=187.0
)

if result:
    print('=== V6.0 标点生成测试 (hearts2hearts flip) ===')
    print('数据来源:', result.get('source'))
    print()
    for key, cue in result['hotcues'].items():
        print(f"{key}: {cue['Start']:6.2f}s | {cue['Name']}")
    print()
    print('验证对比:')
    print('用户手动标点: A=15.16s, B=29.38s')
    a_val = result['hotcues']['A']['Start']
    b_val = result['hotcues']['B']['Start']
    print(f"V6.0 生成:    A={a_val:.2f}s, B={b_val:.2f}s")
    
    # 评估误差
    a_error = abs(a_val - 15.16)
    b_error = abs(b_val - 29.38)
    print()
    print(f"A 点误差: {a_error:.2f}s")
    print(f"B 点误差: {b_error:.2f}s")
    
    if a_error < 3 and b_error < 3:
        print("✅ 测试通过！误差在可接受范围内")
    else:
        print("⚠️ 误差较大，需要调整算法")
else:
    print('生成失败')
