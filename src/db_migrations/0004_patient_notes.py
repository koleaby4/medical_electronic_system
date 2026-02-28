from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)
logger.setLevel("INFO")


@with_logging
def _add_notes_to_patients(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE patients ADD COLUMN notes TEXT;")


def upgrade(conn: sqlite3.Connection) -> None:
    _add_notes_to_patients(conn)


@with_logging
def downgrade(conn: sqlite3.Connection) -> None:
    # SQLite does not support dropping columns easily before 3.35.0,
    # but we can try if it's a recent version or just accept that it might be hard.
    # However, for simplicity and common practice in such small projects:
    try:
        conn.execute("ALTER TABLE patients DROP COLUMN notes;")
    except sqlite3.OperationalError:
        logger.warning(
            "Could not drop column 'notes' from 'patients' table. This might be due to an older SQLite version."
        )
