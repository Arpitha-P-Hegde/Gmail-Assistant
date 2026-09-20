import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mail.db"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            sender TEXT,
            recipient TEXT,
            cc TEXT,
            subject TEXT,
            date TEXT,
            snippet TEXT,
            label_ids TEXT,
            has_attachment INTEGER,
            body_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Older installations were created before categories existed.  SQLite's
    # ADD COLUMN is safe here: it preserves every existing message.
    columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(emails)").fetchall()
    }
    if "category" not in columns:
        cursor.execute("ALTER TABLE emails ADD COLUMN category TEXT")

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)"
    )

    connection.commit()
    connection.close()
