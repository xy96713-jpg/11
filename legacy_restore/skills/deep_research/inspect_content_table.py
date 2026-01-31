
from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def inspect_content_table():
    db = Rekordbox6Database()
    query = text("PRAGMA table_info(djmdContent)")
    results = db.session.execute(query).fetchall()
    print("Columns in djmdContent:")
    for row in results:
        print(f" - {row[1]} (Type: {row[2]})")

if __name__ == "__main__":
    inspect_content_table()
