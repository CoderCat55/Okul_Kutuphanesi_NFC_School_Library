import sqlite3
import os
from contextlib import contextmanager

def get_database_path():
    """Get the database path from environment variable or use default."""
    return os.environ.get('DATABASE_PATH', 'library.db')

@contextmanager
def get_db_connection():
    """Create a database connection context manager.

    Yields:
        sqlite3.Connection: A database connection with row_factory set to sqlite3.Row.

    The connection is automatically closed when exiting the context.
    """
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    print(f"[DEBUG] get_db_connection() opened connection {id(conn)} to {get_database_path()}")  # Debug
    try:
        yield conn
    finally:
        print(f"[DEBUG] get_db_connection() closing connection {id(conn)}")  # Debug
        conn.close()

def init_db():
    """Initialize the database by creating all required tables.

    Returns:
        sqlite3.Connection: The database connection with row_factory set to sqlite3.Row.

    Raises:
        sqlite3.Error: If an error occurs during database initialization.
    """
    db_path = get_database_path()
    print(f"[DEBUG] init_db() connecting to {db_path}")  # Debug
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    print(f"[DEBUG] init_db() connection established")  # Debug
    try:
        cursor = conn.cursor()
        print(f"[DEBUG] init_db() creating students table")  # Debug
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                student_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print(f"[DEBUG] init_db() students table created")  # Debug

        #Tag table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        # Resources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                language TEXT,
                shelf_location TEXT,
                resource_type TEXT NOT NULL
                CHECK (resource_type IN ('physical', 'digital')),
                tags TEXT,
                file_path TEXT,
                nfc_tag TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_available BOOLEAN DEFAULT 1
            )
        ''')
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL
                CHECK (transaction_type IN ('checkout', 'return')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (resource_id) REFERENCES resources (id)
            )
        ''')
        # Activity log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migration: add nfc_tag column if upgrading from an older schema
        # where the resources table was created without it.
        cursor.execute("PRAGMA table_info(resources)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if 'nfc_tag' not in existing_columns:
            print(f"[DEBUG] init_db() migrating: adding nfc_tag column")  # Debug
            cursor.execute('ALTER TABLE resources ADD COLUMN nfc_tag TEXT')
            cursor.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS idx_resources_nfc_tag '
                'ON resources(nfc_tag) WHERE nfc_tag IS NOT NULL'
            )

        print(f"[DEBUG] init_db() committing transaction")  # Debug
        conn.commit()
        print(f"[DEBUG] init_db() transaction committed")  # Debug
    except Exception as e:
        print(f"[DEBUG] init_db() exception: {e}")  # Debug
        conn.close()
        raise
    print(f"[DEBUG] init_db() returning connection")  # Debug
    return conn