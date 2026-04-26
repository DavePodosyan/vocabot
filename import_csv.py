import csv
import sqlite3
from database import get_connection

def import_csv(file_path):
    conn = get_connection()
    cursor = conn.cursor()

    count = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        # Check dialect and reader
        reader = csv.DictReader(csvfile)
        
        # Determine the correct column names for the dataset
        # CEFRJ uses 'headword', 'pos', 'CEFR'
        # Octanove uses 'headword', 'pos', 'CEFR' as well? Let's assume yes based on standard.
        headers = reader.fieldnames
        if not headers or 'headword' not in headers:
            print(f"Skipping {file_path}: Invalid headers: {headers}")
            return
            
        for row in reader:
            word = row.get('headword', '').strip()
            word_type = row.get('pos', '').strip()
            level = row.get('CEFR', 'Unknown').strip()
            
            if not word:
                continue

            # Check if word already exists to avoid massive duplication
            cursor.execute('SELECT id FROM words WHERE word = ? AND word_type = ? AND level = ?', (word, word_type, level))
            if cursor.fetchone():
                continue

            cursor.execute('''
                INSERT INTO words (word, word_type, definition, translation, level, status)
                VALUES (?, ?, '', '', ?, 'new')
            ''', (word, word_type, level))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {count} new words from {file_path}.")

if __name__ == '__main__':
    files_to_import = [
        'cefrj-vocabulary-profile-1.5.csv',
        'octanove-vocabulary-profile-c1c2-1.0.csv'
    ]
    for f in files_to_import:
        import_csv(f)
