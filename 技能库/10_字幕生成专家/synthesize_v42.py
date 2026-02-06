
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
    
    flat_lyric_words = []
    for line_idx, line in enumerate(orig_lines):
        for w in line.split():
            cw = re.sub(r'[^a-z]', '', w.lower())
            flat_lyric_words.append({'orig': w, 'clean': cw, 'line_idx': line_idx, 'start': None, 'end': None})

    # Strict Anchor Selection
    tg_ptr = 0
    for lf in flat_lyric_words:
        if not lf['clean']: continue
        for i in range(tg_ptr, min(tg_ptr + 80, len(tg_words))):
            tw = tg_words[i]
            if lf['clean'] == tw['text'] or (len(lf['clean']) > 3 and (lf['clean'] in tw['text'] or tw['text'] in lf['clean'])):
                lf['start'] = tw['start']
                lf['end'] = tw['end']
                tg_ptr = i + 1
                break

    srt_output = []
    for i, line_text in enumerate(orig_lines):
        line_words = [w for w in flat_lyric_words if w['line_idx'] == i]
        known = [w for w in line_words if w['start'] is not None]
        
        if known:
            # STRICT PHRASING: Lock to exact start and exact end
            l_start = known[0]['start']
            l_end = known[-1]['end']
            
            # If the last word is very short (<0.1s), slightly expand for readability
            if l_end - l_start < 0.6:
                l_end = l_start + 0.8
        else:
            # Interpolation for non-detected segments
            prev_end = srt_output[-1]['end'] if srt_output else 0.0
            next_start = None
            for j in range(i + 1, len(orig_lines)):
                future_known = [w for w in flat_lyric_words if w['line_idx'] == j and w['start'] is not None]
                if future_known:
                    next_start = future_known[0]['start']
                    break
            
            if next_start:
                gap = next_start - prev_end
                unknown_count = 0
                for k in range(i, len(orig_lines)):
                    if not any(w['start'] for w in [x for x in flat_lyric_words if x['line_idx'] == k]): unknown_count += 1
                    else: break
                step = gap / (unknown_count + 1)
                l_start = prev_end + (step * 0.1)
                l_end = prev_end + (step * 0.9)
            else:
                l_start = prev_end + 0.3
                l_end = l_start + 2.0

        # Collision Guard: Ensure min 0.05s gap between subtitles
        if srt_output and l_start < srt_output[-1]['end'] + 0.03:
            l_start = srt_output[-1]['end'] + 0.05
        
        if l_end <= l_start: l_end = l_start + 0.6

        srt_output.append({'start': l_start, 'end': l_end, 'text': line_text})

    # Final Monotonicity & Overlap Polish
    for i in range(len(srt_output) - 1):
        if srt_output[i]['end'] > srt_output[i+1]['start']:
            srt_output[i]['end'] = srt_output[i+1]['start'] - 0.02

    # Save to Desktop
    desktop_path = r"C:\Users\Administrator\Desktop\Timeline 1_V42_MFA_Professional.srt"
    with open(desktop_path, "w", encoding="utf-8") as f:
        for idx, s in enumerate(srt_output):
            f.write(f"{idx+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{s['text']}\n\n")

    print(f"Delivered V42.6 Strict Phrasing SRT to Desktop.")

if __name__ == "__main__":
    synthesize_srt()
