from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def main():
    db = Rekordbox6Database()
    tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'djmd%'")).fetchall()
    table_names = sorted([t[0] for t in tables])
    print("All DJMD Tables:")
    for name in table_names:
        print(f"  - {name}")
        
    # Check for Kind=1 rows in djmdCue to see if they hold HotCue info
    print("\nAnalyzing djmdCue Kind=1 (Suspected HotCues):")
    res = db.session.execute(text("SELECT * FROM djmdCue WHERE Kind=1 LIMIT 5")).fetchall()
    columns = db.session.execute(text("PRAGMA table_info(djmdCue)")).fetchall()
    col_names = [c[1] for c in columns]
    for row in res:
        print(dict(zip(col_names, row)))

if __name__ == "__main__":
    main()
