# db.py
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "parking.db")

def get_conn():
    # check_same_thread=False helps avoid threading errors during development
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ✅ Transactions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_name TEXT,
        vehicle_name TEXT,
        vehicle_type TEXT,
        plate_number TEXT,
        entry_time TEXT,
        exit_time TEXT,
        parking_slot TEXT
    )
    """)

    # ✅ History table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_name TEXT,
        vehicle_name TEXT,
        vehicle_type TEXT,
        plate_number TEXT,
        entry_time TEXT,
        exit_time TEXT,
        parking_slot TEXT
    )
    """)

    conn.commit()
    conn.close()

