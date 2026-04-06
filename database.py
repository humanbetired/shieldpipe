import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "shieldpipe.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id       TEXT UNIQUE NOT NULL,
            project_name  TEXT NOT NULL,
            target_path   TEXT NOT NULL,
            status        TEXT NOT NULL,
            total_critical INTEGER DEFAULT 0,
            total_high     INTEGER DEFAULT 0,
            total_medium   INTEGER DEFAULT 0,
            total_low      INTEGER DEFAULT 0,
            gate_result   TEXT,
            ai_summary    TEXT,
            scanned_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scan_findings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id     TEXT NOT NULL,
            scanner     TEXT NOT NULL,
            severity    TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT,
            file_path   TEXT,
            line_number INTEGER,
            evidence    TEXT,
            cve_id      TEXT,
            created_at  TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    print("[DB] Initialized")

if __name__ == "__main__":
    init_db()