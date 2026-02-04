lines = open('enhanced_harmonic_set_sorter.py', encoding='utf-8').readlines()
try:
    first_indented = [l for l in lines if l.startswith(' ')][0]
    print(f"First indented line starts with: {repr(first_indented[:8])}")
    
    # Check lines around patch
    print("Checking patch area (2840):")
    for i in range(2838, 2845):
        print(f"{i+1}: {repr(lines[i][:16])}")
except Exception as e:
    print(e)
