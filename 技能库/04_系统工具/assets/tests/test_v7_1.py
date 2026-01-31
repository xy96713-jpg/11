
import os
from pathlib import Path
from pyrekordbox import Rekordbox6Database
from auto_hotcue_generator import generate_hotcues

db = Rekordbox6Database()
titles = ['Beautiful Trick', 'Dream in the Night', 'It\'s Like One!']
for title in titles:
    c_list = list(db.get_content(Title=title))
    if not c_list: continue
    c = c_list[0]
    bpm = c.BPM / 100.0
    duration = 300 

    hcs = generate_hotcues(
        audio_file='dummy.mp3',
        bpm=bpm,
        duration=duration,
        content_id=c.ID,
        content_uuid=c.UUID
    )

    print(f'\n--- V7.1 Test: {title} ---')
    cues = hcs.get('hotcues', {})
    for char in ['A', 'B', 'C', 'D', 'E']:
        if char in cues:
            val = cues[char]
            print(f"{char}: {val['Start']:6.3f}s | {val['Name']}")
