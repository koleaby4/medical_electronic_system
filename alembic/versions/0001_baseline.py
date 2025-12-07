"""
Baseline schema creation for SQLite.

This migration creates all tables required by the application:
- patients
- addresses
- medical_checks
- medical_check_items
- medical_check_names
- medical_check_template_items

Downgrade drops them in reverse dependency order.
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=ON;")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            sex TEXT NOT NULL,
            dob DATE NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS addresses (
            patient_id INTEGER PRIMARY KEY,
            line_1 TEXT NOT NULL,
            line_2 TEXT,
            town TEXT NOT NULL,
            postcode TEXT NOT NULL,
            country TEXT NOT NULL,
            FOREIGN KEY(patient_id)
                REFERENCES patients(patient_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_check_names (
            medical_check_name_id INTEGER PRIMARY KEY,
            medical_check_name TEXT NOT NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_checks (
            check_id INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            check_type INTEGER NOT NULL,
            check_date DATE NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY(patient_id)
                REFERENCES patients(patient_id)
                ON DELETE CASCADE ON UPDATE CASCADE
            ,
            FOREIGN KEY(check_type)
                REFERENCES medical_check_names(medical_check_name_id)
                ON UPDATE CASCADE
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id
            ON medical_checks(patient_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id_date
            ON medical_checks(patient_id, check_date);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_check_items (
            check_item_id TEXT PRIMARY KEY,
            check_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            units TEXT,
            value TEXT NOT NULL,
            FOREIGN KEY(check_id)
                REFERENCES medical_checks(check_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_check_items_check_id
            ON medical_check_items(check_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_medical_check_items_name
            ON medical_check_items(name);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_check_template_items (
            medical_check_name_id INTEGER NOT NULL,
            name TEXT,
            units TEXT,
            input_type TEXT,
            placeholder TEXT,
            FOREIGN KEY(medical_check_name_id)
                REFERENCES medical_check_names(medical_check_name_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mct_items_medical_check_name_id
            ON medical_check_template_items(medical_check_name_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_mct_items_medical_check_name_id;")
    op.execute("DROP TABLE IF EXISTS medical_check_template_items;")

    op.execute("DROP TABLE IF EXISTS medical_check_names;")

    op.execute("DROP INDEX IF EXISTS ix_medical_check_items_name;")
    op.execute("DROP INDEX IF EXISTS ix_medical_check_items_check_id;")
    op.execute("DROP TABLE IF EXISTS medical_check_items;")

    op.execute("DROP INDEX IF EXISTS ix_medical_checks_patient_id_date;")
    op.execute("DROP INDEX IF EXISTS ix_medical_checks_patient_id;")
    op.execute("DROP TABLE IF EXISTS medical_checks;")

    op.execute("DROP TABLE IF EXISTS addresses;")

    op.execute("DROP TABLE IF EXISTS patients;")
