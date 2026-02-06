
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
            text = re.sub(r'[^a-z]', '', text)
            if text and text != 'spn':
                words.append({'start': xmin, 'end': xmax, 'text': text})
            i += 4
        else:
            i += 1
    return words

def get_lyrics():
    lyric_file = r"d:\anti\技能库\10_字幕生成专家\lyrics_context.json"
    with open(lyric_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["XG_HYPNOTIZE_PART1"] + data["NewJeans_Super_Shy"] + data["XG_HYPNOTIZE_REPRISE"]

def format_time(seconds):
    if seconds < 0: seconds = 0
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def synthesize_srt():
    tg_words = parse_textgrid(r"d:\anti\技能库\10_字幕生成专家\mfa_output\vocal_track.TextGrid")
    orig_lines = get_lyrics()
    
    # 1. Prepare flat word list from lyrics
    flat_lyric_words = []
    for line_idx, line in enumerate(orig_lines):
        for w in line.split():
            cw = re.sub(r'[^a-z]', '', w.lower())
            flat_lyric_words.append({
                'orig': w,
                'clean': cw,
                'line_idx': line_idx,
                'start': None,
                'end': None
            })

    # 2. Sequential Alignment (The human way: matching one by one, allowing skips)
    tg_ptr = 0
    for lw in flat_lyric_words:
        if not lw['clean']: continue # Skip Korean/Empty
        
        # Look for this word in TG within a reasonable lookahead (e.g. 15 words)
        best_match_idx = -1
        for i in range(tg_ptr, min(tg_ptr + 15, len(tg_words))):
            tw = tg_words[i]
            if lw['clean'] == tw['text'] or (len(lw['clean']) > 3 and (lw['clean'] in tw['text'] or tw['text'] in lw['clean'])):
                best_match_idx = i
                break
        
        if best_match_idx != -1:
            lw['start'] = tg_words[best_match_idx]['start']
            lw['end'] = tg_words[best_match_idx]['end']
            tg_ptr = best_match_idx + 1 # Strictly move forward
            
    # 3. Propagate timing to lines
    final_lines = []
    for i, line in enumerate(orig_lines):
        words = [w for w in flat_lyric_words if w['line_idx'] == i]
        known_words = [w for w in words if w['start'] is not None]
        
        if known_words:
            # Respect musical flow: Start at first word, end at last word
            start = known_words[0]['start']
            end = known_words[-1]['end']
            # Minimal gap check
            if end - start < 1.0: end = start + 1.2 # Human readability
        else:
            # Interpolation logic for missing/Korean lines
            # Anchors from previous and next available lines
            prev_end = final_lines[-1]['end'] if final_lines else 0
            
            next_start = None
            for j in range(i + 1, len(orig_lines)):
                future_words = [w for w in flat_lyric_words if w['line_idx'] == j and w['start'] is not None]
                if future_words:
                    next_start = future_words[0]['start']
                    break
            
            if next_start:
                # Interpolate in the gap
                gap = next_start - prev_end
                # How many non-anchored lines?
                unseen_count = 0
                for k in range(i, len(orig_lines)):
                    if any(w['start'] for w in [x for x in flat_lyric_words if x['line_idx'] == k]): break
                    unseen_count += 1
                
                step = gap / (unseen_count + 1)
                start = prev_end + step * 0.1
                end = prev_end + step * 0.9
            else:
                # Trailing end
                start = prev_end + 0.5
                end = start + 2.0
        
        # FINAL SANITY GUARD: Duration and Overlap
        if final_lines:
            # Ensure no overlap
            if start < final_lines[-1]['end'] + 0.05:
                start = final_lines[-1]['end'] + 0.1
            # Ensure no time travel
            if end <= start:
                end = start + 1.2
                
        final_lines.append({'start': start, 'end': end, 'text': line})

    # Export
    with open(r"C:\Users\Administrator\Desktop\Timeline 1_V42_MFA_Professional.srt", "w", encoding='utf-8') as f:
        for idx, ln in enumerate(final_lines):
            f.write(f"{idx+1}\n{format_time(ln['start'])} --> {format_time(ln['end'])}\n{ln['text']}\n\n")

    print("Synthesized V42.3 with Sequential Sequential Alignment.")

if __name__ == "__main__":
    synthesize_srt()
