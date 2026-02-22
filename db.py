import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "praygpt.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create inputs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_payload TEXT,
            image_path_or_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report TEXT
        )
    ''')

    conn.commit()
    conn.close()

def add_input(text_payload, image_path_or_url=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO inputs (text_payload, image_path_or_url, status)
        VALUES (?, ?, 'pending')
    ''', (text_payload, image_path_or_url))

    input_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return input_id

def get_pending_inputs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM inputs WHERE status = 'pending' ORDER BY created_at ASC
    ''')

    rows = cursor.fetchall()
    inputs = [dict(row) for row in rows]
    conn.close()
    return inputs

def update_input_status(input_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE inputs SET status = ? WHERE id = ?
    ''', (status, input_id))

    conn.commit()
    conn.close()

def save_report_to_db(input_id, report_content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE inputs SET report = ?, status = 'completed' WHERE id = ?
    ''', (report_content, input_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
