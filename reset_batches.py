import sqlite3
from database import get_connection

def reset_batches():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Delete batches and their associations
    cursor.execute('DELETE FROM batch_words')
    cursor.execute('DELETE FROM batches')
    
    # Reset status of words back to 'new', but KEEP definitions/translations
    cursor.execute("UPDATE words SET status = 'new' WHERE status != 'new'")
    
    conn.commit()
    conn.close()
    print("Successfully reset all batches! Definitions and translations were kept intact.")

if __name__ == "__main__":
    reset_batches()
