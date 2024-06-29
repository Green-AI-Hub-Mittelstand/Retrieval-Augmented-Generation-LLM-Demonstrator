import sqlite3

db_path = "crawler/green-ai-projekte.db"
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_schema WHERE type='table'")

tables = cur.fetchall()

print("Tables in the database:")
for table in tables:
    print(table[0])