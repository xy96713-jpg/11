import re

# Read file
with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i in range(2800, 3600): # Focus on the problematic loop
    line = lines[i]
    if 'score +=' in line:
        # Check if it's already safe (checked manually or by previous script)
        if 'or 0' in line or 'else 0' in line:
            continue
        if 'mix_score_safe' in line:
            continue

        match = re.search(r'score \+= (.+)', line)
        if match:
            expr = match.group(1).strip()
            # Wrap everything in ( ... or 0)
            # This handles `var * weight`, `func()`, etc.
            # If expr evaluates to None, `None or 0` is 0? 
            # No! `None or 0` is 0. 
            # BUT `None * 0.5` raises TypeError immediately.
            # So `(None * 0.5) or 0` crashes inside the parens.
            
            # If the expression contains `*`, we assume the variables inside are the issue.
            # But fixing that requires parsing.
            
            # Let's wrap the assignments or just check the variables.
            # But for `score += val`, if val is `None`, then `(val or 0)` is 0.
            
            # If expr is `key_score * key_weight`.
            # If `key_score` is None? -> TypeError.
            # If `key_weight` is None? -> TypeError.
            
            # So `score +=` error means the RHS *evaluated* to None.
            # `key_score * key_weight` will NOT evaluate to None (it returns float or raises error).
            # `int * float` -> float. `None * float` -> Error.
            # So if `score += X` throws `int += None`, then X IS None.
            # It implies X cannot be an expression that raises TypeError on None input.
            # So X MUST be a simple variable or function call that returns None.
            # OR `dict.get(...)`.
            
            # So looking for `score += expr` where `expr` evaluates to None.
            
            # Examples:
            # score += phase_penalty  (Fixed)
            # score += energy_weights[5] (Fixed)
            # score += key_score * key_weight (Evaluates to number or crashes. Not None)
            
            # score += swing_score ? 
            # score += 15 ? (Safe)
            
            # I will wrap ANY remaining `score += var` or `score += dict[...]` or `score += func(...)`.
            
            # Filter comments
            if '#' in expr:
                 expr = expr.split('#')[0].strip()
            
            if not expr: continue
            
            # Skip if it looks like math
            if '*' in expr or '+' in expr or '-' in expr or '/' in expr:
                # Unless it's a function call? `func() + 1` crashes if func returns None.
                continue
                
            # Skip literals
            if expr.isdigit(): continue
            
            # Apply fix
            print(f"Patching line {i+1}: {expr}")
            lines[i] = line.replace(f"score += {expr}", f"score += ({expr} or 0)")
            count += 1

print(f"Patched {count} lines.")
with open('enhanced_harmonic_set_sorter.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
