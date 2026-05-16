import sqlite3
from contextlib import contextmanager

from app.core.config import ARCHIVE_DIR, DATA_DIR, DB_PATH, UPLOAD_DIR


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS speaker_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker_name TEXT NOT NULL,
                embedding_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                note TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inference_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_type TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                audio_hash TEXT,
                mfa_raw_output TEXT NOT NULL,
                rawgat_raw_output TEXT NOT NULL,
                speaker_result TEXT NOT NULL,
                spoof_result TEXT NOT NULL,
                risk_score REAL NOT NULL,
                final_label TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
