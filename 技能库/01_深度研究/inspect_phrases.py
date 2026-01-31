from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

def inspect_phrases():
    db = Rekordbox6Database()
    
    # Check for Phrase table
    query = text("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='djmdPhrase'
    """)
    if not db.session.execute(query).fetchone():
        print("Table 'djmdPhrase' not found.")
        return

    # Sample phrases
    query = text("""
        SELECT 
            p.ContentID,
            c.Title,
            p.InMsec,
            p.Kind,
            p.Num
        FROM djmdPhrase p
        JOIN djmdContent c ON p.ContentID = c.ID
        LIMIT 20
    """)
    results = db.session.execute(query).fetchall()
    
    print("--- Rekordbox Phrase Samples ---")
    for row in results:
        print(row)

if __name__ == "__main__":
    inspect_phrases()
