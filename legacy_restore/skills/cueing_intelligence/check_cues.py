from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def check_cues():
    db = Rekordbox6Database()
    # Get first 10 tracks
    res = db.session.execute(text("SELECT ID, Title FROM djmdContent LIMIT 10")).fetchall()
    
    for row in res:
        content_id = row[0]
        title = row[1]
        print(f"\nTrack: {title} (ID: {content_id})")
        
        # Check djmdCue (Memory Cues)
        cues = db.session.execute(text("SELECT ID, Name, InMsec FROM djmdCue WHERE ContentID = :cid"), {"cid": content_id}).fetchall()
        print(f"  Memory Cues: {len(cues)}")
        for c in cues:
            print(f"    - {c[1]} at {c[2]/1000:.2f}s")
            
        # Check djmdHotCue
        hotcues = db.session.execute(text("SELECT ID, Name, InMsec, HotCueNo FROM djmdHotCue WHERE ContentID = :cid"), {"cid": content_id}).fetchall()
        print(f"  HotCues: {len(hotcues)}")
        for hc in hotcues:
            # HotCueNo 0=A, 1=B, 2=C, 3=D, 4=E, 5=F, 6=G, 7=H
            hc_char = chr(ord('A') + hc[3]) if 0 <= hc[3] <= 7 else str(hc[3])
            print(f"    - HotCue {hc_char} ({hc[1]}) at {hc[2]/1000:.2f}s")

if __name__ == "__main__":
    check_cues()
