"""
Baseline schema creation for SQLite.

This migration creates all tables required by the application:
- patients
- addresses
- medical_checks
- medical_check_items
- medical_check_templates
- medical_check_template_items

Downgrade drops them in reverse dependency order.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure PRAGMA for foreign keys is enabled (safety; env.py also sets it)
    op.execute("PRAGMA foreign_keys=ON;")

    # patients
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

    # addresses (1:1 with patients)
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

    # medical_checks
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_checks (
            check_id INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            check_type TEXT NOT NULL,
            check_date DATE NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY(patient_id)
                REFERENCES patients(patient_id)
                ON DELETE CASCADE ON UPDATE CASCADE
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

    # medical_check_items
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

    # medical_check_templates
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_check_templates (
            template_id INTEGER PRIMARY KEY,
            template_name TEXT NOT NULL
        );
        """
    )

    # medical_check_template_items
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_check_template_items (
            template_id INTEGER NOT NULL,
            name TEXT,
            units TEXT,
            input_type TEXT,
            placeholder TEXT,
            FOREIGN KEY(template_id)
                REFERENCES medical_check_templates(template_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mct_items_template_id
            ON medical_check_template_items(template_id);
        """
    )

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_mct_items_template_id;")
    op.execute("DROP TABLE IF EXISTS medical_check_template_items;")

    op.execute("DROP TABLE IF EXISTS medical_check_templates;")

    op.execute("DROP INDEX IF EXISTS ix_medical_check_items_name;")
    op.execute("DROP INDEX IF EXISTS ix_medical_check_items_check_id;")
    op.execute("DROP TABLE IF EXISTS medical_check_items;")

    op.execute("DROP INDEX IF EXISTS ix_medical_checks_patient_id_date;")
    op.execute("DROP INDEX IF EXISTS ix_medical_checks_patient_id;")
    op.execute("DROP TABLE IF EXISTS medical_checks;")

    op.execute("DROP TABLE IF EXISTS addresses;")

    op.execute("DROP TABLE IF EXISTS patients;")
