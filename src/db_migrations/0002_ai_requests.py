from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)
logger.setLevel("INFO")


@with_logging
def _create_ai_requests(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            model_url TEXT NOT NULL,
            system_prompt_text TEXT NOT NULL,
            request_payload_json JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id)
                REFERENCES patients (patient_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );
        """)
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_requests_patient_id
            ON ai_requests(patient_id);
        """
    )


def upgrade(conn: sqlite3.Connection) -> None:
    _create_ai_requests(conn)


@with_logging
def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS ai_requests;")
