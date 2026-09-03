import os
import sqlite3

DB_PATH = "./data/db_local/psychsync_dev.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables in {DB_PATH}: {sorted(tables)}")
conn.close()
