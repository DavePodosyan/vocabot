import sqlite3
from database import init_db, get_connection

def seed_data():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if we already have words
    cursor.execute('SELECT COUNT(*) FROM words')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"Database already contains {count} words. Skipping seed.")
        conn.close()
        return

    words = [
        ("Hello", "Used as a greeting", "Привет", "greeting"),
        ("Apple", "A round fruit with red or green skin", "Яблоко", "noun"),
        ("Book", "A written or printed work consisting of pages", "Книга", "noun"),
        ("Water", "A colorless, transparent, odorless liquid", "Вода", "noun"),
        ("Friend", "A person whom one knows and with whom one has a bond", "Друг", "noun"),
        ("House", "A building for human habitation", "Дом", "noun"),
        ("Car", "A four-wheeled road vehicle", "Машина", "noun"),
        ("Time", "The indefinite continued progress of existence and events", "Время", "noun"),
        ("Day", "A period of twenty-four hours", "День", "noun"),
        ("Night", "The period of darkness in each twenty-four hours", "Ночь", "noun"),
        ("Good", "To be desired or approved of", "Хороший", "adjective"),
        ("Bad", "Of poor quality or a low standard", "Плохой", "adjective"),
        ("Big", "Of considerable size or extent", "Большой", "adjective"),
        ("Small", "Of a size that is less than normal", "Маленький", "adjective"),
        ("Hot", "Having a high degree of heat", "Горячий", "adjective"),
        ("Cold", "Of or at a low or relatively low temperature", "Холодный", "adjective"),
        ("Fast", "Moving or capable of moving at high speed", "Быстрый", "adjective"),
        ("Slow", "Moving or operating, or designed to do so, only at a low speed", "Медленный", "adjective"),
        ("Happy", "Feeling or showing pleasure or contentment", "Счастливый", "adjective"),
        ("Sad", "Feeling or showing sorrow; unhappy", "Грустный", "adjective"),
    ]

    for word, definition, translation, word_type in words:
        cursor.execute('''
            INSERT INTO words (word, word_type, definition, translation, level, status)
            VALUES (?, ?, ?, ?, 'A1', 'new')
        ''', (word, word_type, definition, translation))
    
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(words)} words into the database.")

if __name__ == '__main__':
    seed_data()
