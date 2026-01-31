from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def list_all_tables():
    db = Rekordbox6Database()
    query = text("SELECT name FROM sqlite_master WHERE type='table'")
    results = db.session.execute(query).fetchall()
    print("Tables in Rekordbox Database:")
    for row in sorted(row[0] for row in results):
        print(f" - {row}")

if __name__ == "__main__":
    list_all_tables()
