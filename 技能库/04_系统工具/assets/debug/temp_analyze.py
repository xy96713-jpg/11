#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析用户习惯与 PSSI 段落的对应关系"""

from core.rekordbox_phrase_reader import RekordboxPhraseReader

reader = RekordboxPhraseReader()
phrases = reader.get_phrases('fcb46903-42a0-4b86-8904-41920b7cc6a8', 128.0)

print('=== hearts2hearts flip 段落数据 ===')
for p in phrases[:6]:
    time_val = p["time"]
    kind_val = p["kind"]
    print(f'{time_val:6.2f}s | {kind_val}')

print()
print('用户标点: A=15.16s, B=29.38s')
print()
print('分析:')
print('  - Intro 在 0.47s')
print('  - Up 在 5.16s')
print('  - Down 在 16.41s (用户 A 点在 15.16s，正好在 Down 前 1.25s)')
print('  - Buildup 在 27.66s (用户 B 点在 29.38s，在 Buildup 后 1.72s)')
print()
print('结论:')
print('  用户习惯：A 点 = Down 段落起点前 8 beats')
print('           B 点 = Buildup 段落起点')
