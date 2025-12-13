"""
Baseline schema migration.

Version id: 0001_baseline
Previous: 0000

Defines upgrade() and downgrade() for the initial schema.

This version splits the upgrade into small, named steps and logs progress so
that, if anything fails, it is easy to see which step succeeded and which one
failed.
"""

from __future__ import annotations

import sqlite3
from logging import getLogger

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)
logger.setLevel("INFO")


@with_logging
def _pragma_foreign_keys_on(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON;")


@with_logging
def _create_patients(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY,
            title       TEXT    NOT NULL,
            first_name  TEXT    NOT NULL,
            middle_name TEXT,
            last_name   TEXT    NOT NULL,
            sex         TEXT    NOT NULL,
            dob         DATE    NOT NULL,
            email       TEXT    NOT NULL,
            phone       TEXT    NOT NULL
        );
        """)


@with_logging
def _create_addresses(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            patient_id INTEGER PRIMARY KEY,
            line_1     TEXT    NOT NULL,
            line_2     TEXT,
            town       TEXT    NOT NULL,
            postcode   TEXT    NOT NULL,
            country    TEXT    NOT NULL,
            FOREIGN KEY (patient_id)
                REFERENCES patients (patient_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );

        """)


@with_logging
def _create_medical_check_types(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medical_check_types (
            type_id INTEGER PRIMARY KEY,
            name    TEXT    NOT NULL
);
        """)


@with_logging
def _create_medical_checks(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medical_checks (
            check_id   INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            type_id    INTEGER NOT NULL,
            check_date DATE    NOT NULL,
            status     TEXT    NOT NULL,
            notes      TEXT,
            FOREIGN KEY (patient_id)
                REFERENCES patients (patient_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (type_id)
                REFERENCES medical_check_types (type_id)
                ON UPDATE CASCADE
        );
        """)

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id
            ON medical_checks(patient_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id_date
            ON medical_checks(patient_id, check_date);
        """
    )


@with_logging
def _create_medical_check_items(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medical_check_items (
            check_item_id TEXT    PRIMARY KEY,
            check_id      INTEGER NOT NULL,
            name          TEXT    NOT NULL,
            units         TEXT,
            value         TEXT    NOT NULL,
            FOREIGN KEY (check_id)
                REFERENCES medical_checks (check_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );

        """)
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_check_items_check_id
            ON medical_check_items(check_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_check_items_name
            ON medical_check_items(name);
        """
    )


@with_logging
def _create_medical_check_type_items(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medical_check_type_items (
            type_id     INTEGER NOT NULL,
            name        TEXT,
            units       TEXT,
            input_type  TEXT,
            placeholder TEXT,
            FOREIGN KEY (type_id)
                REFERENCES medical_check_types (type_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );

        """)
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mct_type_items_type_id
            ON medical_check_type_items(type_id);
        """
    )


def upgrade(conn):
    _pragma_foreign_keys_on(conn)
    _create_patients(conn)
    _create_addresses(conn)
    _create_medical_check_types(conn)
    _create_medical_checks(conn)
    _create_medical_check_items(conn)
    _create_medical_check_type_items(conn)


@with_logging
def downgrade(conn):
    conn.executescript(
        """
        PRAGMA foreign_keys=OFF;
        DROP TABLE IF EXISTS medical_check_type_items;
        DROP TABLE IF EXISTS medical_check_items;
        DROP TABLE IF EXISTS medical_checks;
        DROP TABLE IF EXISTS medical_check_types;
        DROP TABLE IF EXISTS addresses;
        DROP TABLE IF EXISTS patients;
        PRAGMA foreign_keys=ON;
        """
    )
