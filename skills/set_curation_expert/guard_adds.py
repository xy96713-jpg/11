import re

# Read file
with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i in range(2800, 3600): # Focus on the problematic loop
    line = lines[i]
    if 'score +=' in line:
        # Check if it's already safe (contains 'if ... else 0' or 'or 0')
        if 'or 0' in line or 'else 0' in line:
            continue
            
        # Extract the expression added
        # score += expr
        match = re.search(r'score \+= (.+)', line)
        if match:
            expr = match.group(1).strip()
            # Wrap in safe check
            # Be careful with comments
            comment = ""
            if '#' in expr:
                 parts = expr.split('#')
                 expr = parts[0].strip()
                 comment = "  #" + parts[1]
            
            # Don't wrap literals
            if expr.replace('.', '', 1).isdigit() or (expr.startswith('-') and expr[1:].replace('.', '', 1).isdigit()):
                continue

            # Wrap: score += (expr or 0)
            new_line = line.replace(f"score += {expr}", f"score += ({expr} or 0)")
            # Re-attach comment if needed? match group captured line suffix.
            # Actually, `replace` on the line string is safer if unique.
            
            # Simple replace: `score += X` -> `score += (X or 0)`
            # But X might be complex.
            # Let's just handle simple variables or dict lookups.
            
            # Case 1: `score += variable`
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', expr):
                 lines[i] = line.replace(f"score += {expr}", f"score += ({expr} or 0)")
                 count += 1
                 print(f"Patched line {i+1}: {expr}")
            
            # Case 2: `score += dict[key]`
            elif re.match(r'^[a-zA-Z_]+\s*\[.+\]$', expr):
                 lines[i] = line.replace(f"score += {expr}", f"score += ({expr} or 0)")
                 count += 1
                 print(f"Patched line {i+1}: {expr}")

print(f"Patched {count} lines.")
with open('enhanced_harmonic_set_sorter.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
