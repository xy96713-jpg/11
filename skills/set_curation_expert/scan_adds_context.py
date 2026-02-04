try:
    with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if 'score +=' in line:
            # Simple heuristic to identify variable additions
            if '+=' in line and not any(char.isdigit() for char in line.split('+=')[1]):
                 # Likely a variable addition (logic: no digits on RHS)
                 # Actually, let's print everything.
                 context = "".join(lines[max(0, i-2):min(len(lines), i+3)])
                 print(f"--- Line {i+1} ---\n{context}\n")
except Exception as e:
    print(e)
