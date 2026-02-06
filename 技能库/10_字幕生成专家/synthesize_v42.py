
import re
import json
from pathlib import Path

def parse_textgrid(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    words = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('intervals ['):
            xmin = float(lines[i+1].split('=')[1].strip())
            xmax = float(lines[i+2].split('=')[1].strip())
            text = lines[i+3].split('=')[1].strip().strip('"').lower()
            if text:
                words.append({'start': xmin, 'end': xmax, 'text': text})
            i += 4
        else:
            i += 1
    return words

def get_lyrics():
    lyric_file = r"d:\anti\技能库\10_字幕生成专家\lyrics_context.json"
    with open(lyric_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_lines = []
    for part in ["XG_HYPNOTIZE_PART1", "NewJeans_Super_Shy", "XG_HYPNOTIZE_REPRISE"]:
        all_lines.extend(data[part])
    return all_lines

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds * 1000) % 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def synthesize_srt():
    tg_words = parse_textgrid(r"d:\anti\技能库\10_字幕生成专家\mfa_output\vocal_track.TextGrid")
    orig_lines = get_lyrics()
    
    srt_entries = []
    word_idx = 0
    
    for line_idx, line in enumerate(orig_lines):
        # Extract individual words (English and Korean)
        raw_words = line.split()
        line_start = None
        line_end = None
        
        assigned_words = []
        
        for rw in raw_words:
            clean_rw = re.sub(r'[^a-zA-Z\']', '', rw).lower()
            if clean_rw and word_idx < len(tg_words):
                # Try to find a match or just take the next one if it's English
                # Note: MFA might have split "runnin'from" into one word, we need to be careful
                # But for simplicity, we consume tg_words sequentially.
                
                # Check if current tg_word roughly matches clean_rw
                # (Due to cleaning some symbols might differ)
                tg_w = tg_words[word_idx]
                
                # Assign timestamp
                assigned_words.append({
                    'text': rw,
                    'start': tg_w['start'],
                    'end': tg_w['end']
                })
                
                if line_start is None: line_start = tg_w['start']
                line_end = tg_w['end']
                word_idx += 1
            else:
                # Korean or non-English word
                # We'll interpolate its time later or use previous/next
                assigned_words.append({
                    'text': rw,
                    'start': None,
                    'end': None
                })
        
        # Interpolate missing timestamps (Korean/CJK)
        # Simply spread them between the nearest English timestamps
        for i, aw in enumerate(assigned_words):
            if aw['start'] is None:
                # Special case: First word is Korean
                if i == 0:
                    # Look ahead for first timestamp
                    for j in range(len(assigned_words)):
                        if assigned_words[j]['start'] is not None:
                            aw['start'] = max(0, assigned_words[j]['start'] - 0.5)
                            aw['end'] = assigned_words[j]['start']
                            break
                    if aw['start'] is None: # Whole line is Korean (shouldn't happen with MFA input)
                        aw['start'] = line_start if line_start else 0
                        aw['end'] = line_end if line_end else 0
                else:
                    prev_end = assigned_words[i-1]['end']
                    # Look ahead for next timestamp
                    next_start = None
                    for j in range(i+1, len(assigned_words)):
                        if assigned_words[j]['start'] is not None:
                            next_start = assigned_words[j]['start']
                            break
                    
                    if next_start:
                        aw['start'] = prev_end
                        aw['end'] = next_start
                    else:
                        aw['start'] = prev_end
                        aw['end'] = prev_end + 0.3 # Default duration for Korean syllable/word
        
        if assigned_words:
            actual_start = min(w['start'] for w in assigned_words if w['start'] is not None)
            actual_end = max(w['end'] for w in assigned_words if w['end'] is not None)
            
            # Compensation for singing trailing
            actual_end += 0.2
            
            srt_entries.append({
                'index': len(srt_entries) + 1,
                'start': actual_start,
                'end': actual_end,
                'text': line
            })

    # Write SRT
    with open(r"d:\anti\技能库\10_字幕生成专家\Timeline 1_V42_MFA_Professional.srt", "w", encoding='utf-8') as f:
        for entry in srt_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{format_time(entry['start'])} --> {format_time(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"Generated Professional SRT: Timeline 1_V42_MFA_Professional.srt")

if __name__ == "__main__":
    synthesize_srt()
