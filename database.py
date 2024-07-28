import sqlite3

def setup_database(db_path='file_operations.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            operation TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database setup completed.")

def log_operation(file_path, operation, status, db_path='file_operations.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO operations (file_path, operation, status)
        VALUES (?, ?, ?)
    ''', (file_path, operation, status))
    conn.commit()
    conn.close()
    print(f"Logged operation: {file_path}, {operation}, {status}")

def fetch_all_operations(db_path='file_operations.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM operations')
    rows = cursor.fetchall()
    conn.close()
    return rows
