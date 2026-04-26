import sqlite3
import os

DB_PATH = 'vocab.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create Words table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        word_type TEXT,
        definition TEXT,
        translation TEXT,
        level TEXT DEFAULT 'A1',
        status TEXT DEFAULT 'new' -- 'new', 'learning', 'known'
    )
    ''')

    # Create Batches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create Batch_Words pivot table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS batch_words (
        batch_id INTEGER,
        word_id INTEGER,
        FOREIGN KEY (batch_id) REFERENCES batches (id),
        FOREIGN KEY (word_id) REFERENCES words (id),
        PRIMARY KEY (batch_id, word_id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
