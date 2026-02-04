lines = open('enhanced_harmonic_set_sorter.py', encoding='utf-8').readlines()

# We look for the specific artifacts we introduced
# 1. '            try:\n' around 2840
# 2. '            except Exception:\n' around 3634

new_lines = []
skip_next = False
indented_count = 0

for i, line in enumerate(lines):
    if i == 2840 and line.strip() == 'try:':
        print("Found try at 2840, removing.")
        continue
    
    # Check for the except block
    if line.strip() == 'except Exception:' and lines[i+1].strip() == 'continue':
        print(f"Found except at {i}, removing.")
        skip_next = True
        continue
    
    if skip_next:
        skip_next = False
        continue

    # Dedent logic:
    # We indented lines between the try and the except.
    # The try was at 2840. The indented lines started at 2841.
    # The except was around 3634.
    # So lines 2841 to 3633 (inclusive) should be dedented.
    # BUT we need to check if they start with 4 spaces to be safe.
    
    # Also, we check line content to be sure we are in the range.
    # Actually, we can just dedent IF it matches the range we processed.
    # In the previous script: start_idx=2840 (0-indexed), end_idx matched 'candidate_results.append({'
    
    # Current line indices have shifted because of the inserted 'try'.
    # 2840 was 'try'. 2841 is the first indented line.
    # The indented block goes until the line before 'except'.
    
    # Let's simple check: if 2841 <= i <= 3633 (approx), and starts with 12 spaces (was 8, now 12)
    # Be careful not to dedent lines that weren't indented.
    
    # Safe heuristic: strict range based on known markers.
    
    if 2840 < i < 3634: 
        if line.startswith('            '): # 12 spaces
             new_lines.append(line[4:])
             indented_count += 1
        else:
             # This line wasn't indented? Or already had fewer spaces?
             # Just keep it.
             new_lines.append(line)
    else:
        new_lines.append(line)

print(f"Dedented {indented_count} lines.")

with open('enhanced_harmonic_set_sorter.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
