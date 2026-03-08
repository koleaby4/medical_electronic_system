from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)


@with_logging
def upgrade(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voice_recordings (
            voice_recording_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            check_id            INTEGER NOT NULL,
            file_path           TEXT    NOT NULL,
            full_text           TEXT,
            summary             TEXT,
            FOREIGN KEY (check_id)
                REFERENCES medical_checks (check_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS ix_voice_recordings_check_id
            ON voice_recordings(check_id);
    """)


@with_logging
def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS voice_recordings;")
