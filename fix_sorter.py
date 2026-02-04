import sys
from pathlib import Path

path = Path(r'D:\anti\技能库\03_DJ智能助手\assets\enhanced_harmonic_set_sorter.py')
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Indent loop body
# Line 2787 (try:) is at index 2786.
# Content to indent starts at line 2813 (index 2812) and ends at line 3658 (index 3657).
for i in range(2812, 3658):
    lines[i] = '    ' + lines[i]

# Insert except block
# Insert after line 3658 (index 3657), so at index 3658.
lines.insert(3658, '            except Exception as e:\n')
lines.insert(3659, '                if progress_logger:\n')
lines.insert(3660, '                    title = track.get("title", "Unknown")[:40]\n')
lines.insert(3661, '                    progress_logger.log(f"跳过故障音轨 {title}: {e}", console=False)\n')
lines.insert(3662, '                continue\n')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Successfully applied try-except wrapper and indentation fix.")
