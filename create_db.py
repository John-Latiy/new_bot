# create_db.py

import sqlite3
import os

DB_PATH = "data/processed.db"
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_hash TEXT UNIQUE
    )
""")

conn.commit()
conn.close()

print("✅ Таблица processed успешно создана.")
