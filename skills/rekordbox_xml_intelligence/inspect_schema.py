from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def inspect_content_schema():
    db = Rekordbox6Database()
    query = text("PRAGMA table_info(djmdContent)")
    results = db.session.execute(query).fetchall()
    print("Schema of djmdContent:")
    for row in results:
        # row[1] is name, row[2] is type
        print(f" - {row[1]} ({row[2]})")

if __name__ == "__main__":
    inspect_content_schema()
