import sqlite3
import sys

def migrate():
    conn = sqlite3.connect('vocab.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE words ADD COLUMN word_type TEXT")
        print("Successfully added word_type column to words table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column word_type already exists.")
        else:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
