"""Initial SQLite schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-12-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Patients
    op.create_table(
        "patients",
        sa.Column("patient_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("middle_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("sex", sa.String(), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
    )

    # Medical checks
    op.create_table(
        "medical_checks",
        sa.Column("check_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("check_type", sa.String(), nullable=False),
        sa.Column("check_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], name="fk_medical_checks_patients"),
    )
    op.create_index(
        "idx_medical_checks_patient_date",
        "medical_checks",
        ["patient_id", "check_date"],
    )

    # Addresses
    op.create_table(
        "addresses",
        sa.Column("address_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("line_1", sa.String(), nullable=False),
        sa.Column("line_2", sa.String(), nullable=True),
        sa.Column("town", sa.String(), nullable=False),
        sa.Column("postcode", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], name="fk_addresses_patients"),
    )

    # Medical check items
    op.create_table(
        "medical_check_items",
        sa.Column("check_item_id", sa.String(), primary_key=True),  # store UUID as text
        sa.Column("check_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("units", sa.String(), nullable=False, server_default=""),
        sa.Column("value", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["check_id"], ["medical_checks.check_id"], name="fk_items_checks"),
    )
    op.create_index("idx_medical_check_items_check", "medical_check_items", ["check_id"])
    op.create_index("idx_medical_check_items_name", "medical_check_items", ["name"])


def downgrade() -> None:
    op.drop_index("idx_medical_check_items_name", table_name="medical_check_items")
    op.drop_index("idx_medical_check_items_check", table_name="medical_check_items")
    op.drop_table("medical_check_items")
    op.drop_table("addresses")
    op.drop_index("idx_medical_checks_patient_date", table_name="medical_checks")
    op.drop_table("medical_checks")
    op.drop_table("patients")
