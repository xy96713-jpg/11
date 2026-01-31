from pyrekordbox import Rekordbox6Database
from sqlalchemy import text
import json

def main():
    db = Rekordbox6Database()
    table_name = 'djmdCue'
    print(f"--- Deep Inspection: {table_name} ---")
    columns = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = [c[1] for c in columns]
    
    # Get Kind=1 (HotCues?) rows
    hotcue_rows = db.session.execute(text(f"SELECT * FROM {table_name} WHERE Kind=1 LIMIT 5")).fetchall()
    print("\n--- Kind=1 Rows (Suspected HotCues) ---")
    for row in hotcue_rows:
        d = dict(zip(col_names, row))
        print(json.dumps(d, indent=2, default=str))

    # Get Kind=0 (Memory Cues?) rows
    memcue_rows = db.session.execute(text(f"SELECT * FROM {table_name} WHERE Kind=0 LIMIT 5")).fetchall()
    print("\n--- Kind=0 Rows (Suspected Memory Cues) ---")
    for row in memcue_rows:
        d = dict(zip(col_names, row))
        print(json.dumps(d, indent=2, default=str))

if __name__ == "__main__":
    main()
