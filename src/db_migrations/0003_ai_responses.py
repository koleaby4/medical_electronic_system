from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)
logger.setLevel("INFO")


@with_logging
def _create_ai_responses(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            response_json JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id)
                REFERENCES ai_requests (id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );
        """)
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_responses_request_id
            ON ai_responses(request_id);
        """
    )


def upgrade(conn: sqlite3.Connection) -> None:
    _create_ai_responses(conn)


@with_logging
def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS ai_responses;")
