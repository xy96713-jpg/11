from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def find_d_song_tracks():
    db = Rekordbox6Database()
    query = text("""
        SELECT Title, FolderPath, FileNameL, ID 
        FROM djmdContent 
        WHERE FolderPath LIKE 'D:/song%'
        LIMIT 20
    """)
    res = db.session.execute(query).fetchall()
    print("--- D:/song Tracks Inspection ---")
    for r in res:
        print(f"ID: {r.ID}")
        print(f"Title: {r.Title}")
        print(f"Folder: {r.FolderPath}")
        print(f"File: {r.FileNameL}")
        print("-" * 20)

if __name__ == "__main__":
    find_d_song_tracks()
