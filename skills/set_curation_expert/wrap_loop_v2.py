lines = open('enhanced_harmonic_set_sorter.py', encoding='utf-8').readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    # Match EXACTLY the line we want to start try block BEFORE
    # Line 2841: score = -boutique_penalty (approx)
    if 'score = -boutique_penalty' in line and i > 2800 and i < 2900:
        start_idx = i
    
    # Match the END of the loop body
    # We want to include candidate_results.append({...})
    # Line 3633: candidate_results.append({
    # We also have the debug reporter block AFTER it.
    # Lines 3641-3652+
    # The loop ends when we dedent or hit the debug print.
    # Actually, we can just wrap the WHOLE thing until the sorting happens?
    
    # candidate_debug appends to debug_candidate_scores.
    # But checking Indent is hard.
    
    # However, we know checking the `candidate_results.append` is safe enough for logic.
    # We can skip the `debug_reporter` part if it crashes (unlikely).
    # Or strict: The loop MUST execute completely for valid logic.
    
    # Let's find the end of the loop body by indentation.
    # The loop starts with `for track in candidate_tracks:` at ~2806?
    # Let's check line 2800-2810.
    pass

# Read again to find loop start
for i in range(2750, 2850):
     if 'for track in candidate_tracks:' in lines[i]:
         loop_start = i
         break

if loop_start:
    # Loop body starts at loop_start + 1. Indentation should be 12 spaces.
    body_start = loop_start + 1
    
    # Find where indentation drops back to 8 spaces
    for j in range(body_start, len(lines)):
        if lines[j].strip() and not lines[j].startswith('            '):
             # Found shorter indentation (e.g. 8 spaces `candidate_results.sort`)
             # But wait, comments/empty lines might confuse.
             # Only check lines with content.
             body_end = j - 1
             break
    
    print(f"Loop body: {body_start+1} to {body_end+1}")
    
    # Check if lines have 12 spaces
    # Wrap lines body_start to body_end
    
    # Dedent check
    # lines[body_start] must start with 12 spaces.
    
    new_lines = []
    new_lines.extend(lines[:body_start])
    new_lines.append("            try:\n")
    
    for k in range(body_start, body_end + 1):
        if lines[k].strip():
             new_lines.append("    " + lines[k])
        else:
             new_lines.append(lines[k]) # Empty lines don't need indent but whatever
             
    new_lines.append("            except Exception:\n")
    new_lines.append("                continue\n")
    new_lines.extend(lines[body_end+1:])
    
    with open('enhanced_harmonic_set_sorter.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Wrapped successfully.")

else:
    print("Loop not found.")
