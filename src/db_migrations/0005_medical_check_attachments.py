from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)


@with_logging
def upgrade(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medical_check_attachments (
            attachment_id  INTEGER PRIMARY KEY,
            check_id       INTEGER NOT NULL,
            filename       TEXT    NOT NULL,
            content_type   TEXT,
            file_path      TEXT    NOT NULL,
            parsed_content TEXT,
            FOREIGN KEY (check_id)
                REFERENCES medical_checks (check_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS ix_medical_check_attachments_check_id
            ON medical_check_attachments(check_id);
    """)


@with_logging
def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS medical_check_attachments;")
