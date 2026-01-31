
import os
from pathlib import Path
from pyrekordbox import Rekordbox6Database
from auto_hotcue_generator import generate_hotcues

db = Rekordbox6Database()
c_list = list(db.get_content(Title='Dream in the Night'))
if not c_list:
    print('Track not found')
    exit()
c = c_list[0]
bpm = c.BPM / 100.0
duration = 333 

hcs = generate_hotcues(
    audio_file="dummy.mp3",
    bpm=bpm,
    duration=duration,
    content_id=c.ID,
    content_uuid=c.UUID
)

print('--- V7.0 Test Results ---')
cues = hcs.get('hotcues', {})
for char in ['A', 'B', 'C', 'D', 'E']:
    if char in cues:
        val = cues[char]
        print(f"{char}: {val['Start']:6.3f}s | {val['Name']}")

# Accuracy Check
anchor = 0.442
beat_dur = 60.0 / bpm
for char in ['A', 'B', 'E']:
    t = cues[char]['Start']
    dist = (t - anchor) / beat_dur
    print(f"[Align Check] {char} dist from grid: {abs(dist - round(dist)):.10f} beats")
