from pyrekordbox import Rekordbox6Database
from sqlalchemy import text
import json

def main():
    db = Rekordbox6Database()
    table_name = 'djmdHotCueBanklist'
    print(f"--- Inspection: {table_name} ---")
    columns = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = [c[1] for c in columns]
    print(f"Columns: {col_names}")
    
    sample = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 5")).fetchall()
    for row in sample:
        d = dict(zip(col_names, row))
        print(json.dumps(d, indent=2, default=str))

if __name__ == "__main__":
    main()
