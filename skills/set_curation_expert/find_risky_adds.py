import re
try:
    with open('enhanced_harmonic_set_sorter.py', 'r', encoding='utf-8') as f:
        code = f.read()

    print("Checking score += variable...")
    # Matches "score += variable" (ignoring whitespace)
    # Exclude literals (digits)
    matches = re.finditer(r'score\s*\+=\s*([a-zA-Z_][a-zA-Z0-9_]*)', code)
    for m in matches:
        var = m.group(1)
        # Context
        start = max(0, m.start() - 50)
        end = min(len(code), m.end() + 50)
        context = code[start:end].replace('\n', ' ')
        print(f"Var: {var} | Context: {context}")
except Exception as e:
    print(e)
