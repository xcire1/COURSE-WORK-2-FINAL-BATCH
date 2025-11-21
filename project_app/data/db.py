import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\erick\Desktop\CST1510 COURSE WORK 2\DATA") / "intelligence_platform.db"

def connect_database(db_path=DB_PATH):
    """Connect to SQLite database."""
    return sqlite3.connect(str(db_path))
connect_database(DB_PATH)
