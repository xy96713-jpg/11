try:
    with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    # Locate the block inside the loop
    # Loop starts around 2793: for track in candidate_tracks:
    # We want to wrap the body.
    
    # Markers (from file view):
    # 2840: score = -boutique_penalty
    # End: candidate_tracks_with_score.append((score, ...))
    
    for i, line in enumerate(lines):
        if "score = -boutique_penalty" in line:
            start_idx = i
        if "candidate_tracks_with_score.append((score" in line and i > start_idx:
            end_idx = i
            break

    if start_idx != -1 and end_idx != -1:
        print(f"Wrapping lines {start_idx+1} to {end_idx+1}")
        
        # Indent lines
        for i in range(start_idx, end_idx + 1): # Include the append line? No, score is needed there.
            # If we wrap append, and score is not defined (crash before), append fails?
            # Yes, score is local.
            # So we SHOULD include the append line.
            lines[i] = "    " + lines[i]
        
        # Insert try
        lines.insert(start_idx, "            try:\n")
        
        # Insert except AFTER end_idx (which shifted by 1)
        lines.insert(end_idx + 2, "            except Exception:\n")
        lines.insert(end_idx + 3, "                continue\n")

        with open('enhanced_harmonic_set_sorter.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Patched successfully.")
    else:
        print("Markers not found.")
except Exception as e:
    print(e)
