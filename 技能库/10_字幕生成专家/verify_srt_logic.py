
import re
from datetime import datetime

def srt_time_to_seconds(time_str):
    td = datetime.strptime(time_str.replace(',', '.'), '%H:%M:%S.%f') - datetime.strptime('00:00:00', '%H:%M:%S')
    return td.total_seconds()

def audit_srt(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    errors = []
    prev_end = -1
    
    for i, block in enumerate(blocks):
        lines = block.split('\n')
        if len(lines) < 3: continue
        
        idx = lines[0]
        time_range = lines[1]
        text = " ".join(lines[2:])
        
        start_str, end_str = time_range.split(' --> ')
        start = srt_time_to_seconds(start_str)
        end = srt_time_to_seconds(end_str)
        duration = end - start
        
        # 1. Monotonicity check
        if start < prev_end:
            errors.append(f"Block {idx}: Time reversal! Starts at {start}s, previous ended at {prev_end}s.")
        
        # 2. Duration check
        if duration <= 0:
            errors.append(f"Block {idx}: Zero or negative duration ({duration}s).")
        if duration < 0.5:
            errors.append(f"Block {idx}: Flickering alert ({duration}s).")
        if duration > 10.0:
            errors.append(f"Block {idx}: Immense duration alert ({duration}s) - high risk of desync.")
            
        # 3. Speech Rate (WPM/CPS) check
        char_count = len(text)
        word_count = len(text.split())
        cps = char_count / duration if duration > 0 else 0
        wpm = (word_count * 60) / duration if duration > 0 else 0
        
        if wpm > 450: # Extremly fast Rap
             errors.append(f"Block {idx}: Speed light ({wpm:.1f} WPM) - check if words are skipped.")
        if wpm < 5 and duration > 3:
             errors.append(f"Block {idx}: Sloth alert ({wpm:.1f} WPM) - likely stretching over silence.")
             
        prev_end = end

    if not errors:
        print("✅ SRT Logic Audit: 100% CLEAN. No reversals, overlaps, or illogical durations found.")
    else:
        print(f"❌ SRT Audit Found {len(errors)} Issues:")
        for e in errors[:10]: print(f"  - {e}")

if __name__ == "__main__":
    audit_srt(r"C:\Users\Administrator\Desktop\Timeline 1_V42_MFA_Professional.srt")
