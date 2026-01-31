from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def debug_paths():
    db = Rekordbox6Database()
    # Find tracks with real-looking titles
    query = text("""
        SELECT Title, FileNameL, FolderPath, ID 
        FROM djmdContent 
        WHERE Title NOT LIKE '%-%' 
        AND length(Title) > 10
        LIMIT 20
    """)
    res = db.session.execute(query).fetchall()
    print("--- Database Content Inspection ---")
    for r in res:
        print(f"ID: {r.ID}")
        print(f"Title: {r.Title}")
        print(f"File: {r.FileNameL}")
        print(f"Folder: {r.FolderPath}")
        print("-" * 20)

if __name__ == "__main__":
    debug_paths()
