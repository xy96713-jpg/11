from pyrekordbox import Rekordbox6Database
from sqlalchemy import text

db = Rekordbox6Database()

# 精确搜索指定的三首音轨
searches = [
    'LE SSERAFIM Perfect Night (NΣΣT Remix)',
    'MAMAMOO - HIP(JXXXXX edit)',
    'Twice - Tt (Visrah X Noguchii Remix)'
]

for s in searches:
    # 使用参数化查询防止引号问题
    query = text("SELECT ID, Title, FolderPath, FileNameL FROM djmdContent WHERE Title LIKE :term")
    rows = db.session.execute(query, {"term": f"%{s}%"}).fetchall()
    for r in rows:
        print(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}")
    if not rows:
        print(f"NOT FOUND: {s}")
