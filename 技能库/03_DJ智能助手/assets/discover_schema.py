from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def main():
    db = Rekordbox6Database()
    table_name = 'djmdCue'
    print(f"\n--- Table: {table_name} ---")
    columns = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = [c[1] for c in columns]
    print("Full Column List:")
    for c in col_names:
        print(f"  - {c}")
    
    # Check Kind values
    kinds = db.session.execute(text(f"SELECT DISTINCT Kind FROM {table_name}")).fetchall()
    print(f"\nDistinct Kind values: {[k[0] for k in kinds]}")
    
    # Check sample data for each Kind
    for (kind,) in kinds:
        print(f"\nSample for Kind={kind}:")
        sample = db.session.execute(text(f"SELECT * FROM {table_name} WHERE Kind = :k LIMIT 1"), {"k": kind}).fetchone()
        if sample:
            row_dict = dict(zip(col_names, sample))
            print(f"  {row_dict}")

if __name__ == "__main__":
    main()
