from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

db = Rekordbox6Database()

# 搜索用户指定的三首音轨
searches = ['Perfect Night', 'HIP', 'TT']
for s in searches:
    rows = db.session.execute(text(f"SELECT ID, Title FROM djmdContent WHERE Title LIKE '%{s}%' LIMIT 5")).fetchall()
    for r in rows:
        print(f"{r[0]}|{r[1]}")
    print("---")
