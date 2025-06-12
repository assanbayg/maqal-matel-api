import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any

DATABASE_URL = "maqal_matel.db"


def init_db():
    """Create database and load all maqal-matel in JSON"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Create table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS maqal_matelder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            topics TEXT NOT NULL, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute("SELECT COUNT(*) FROM maqal_matelder")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Loading data from JSON...")

        with open("data/maqal_matel_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for maqal in data:
            cursor.execute(
                """
                INSERT INTO maqal_matelder (text, topics)
                VALUES (?, ?)
                       """,
                (maqal["text"], json.dumps(maqal["topics"])),
            )

        print(f"{len(data)} мақал-мәтел салынды!")

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
