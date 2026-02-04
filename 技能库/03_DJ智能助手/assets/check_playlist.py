
import os
import sys
from pyrekordbox import db6

def test_db():
    try:
        db = db6.Rekordbox6Database()
        all_content = list(db.get_content())
        if all_content:
            c = all_content[0]
            print(f"Attributes of Content object: {dir(c)}")
            # Try some common ones
            for attr in ['FilePath', 'file_path', 'Path', 'path', 'Location', 'location']:
                if hasattr(c, attr):
                    print(f"Found attribute: {attr} = {getattr(c, attr)}")
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    test_db()
