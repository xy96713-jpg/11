import re

try:
    with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("Checking for score += ...")
    for i, line in enumerate(lines):
        if 'score +=' in line:
            content = line.strip()
            print(f"{i+1}: {content}")
except Exception as e:
    print(f"Error: {e}")
