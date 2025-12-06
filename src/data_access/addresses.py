from __future__ import annotations

import sqlite3

from src.data_access.base import BaseStorage
from src.models.address import Address


class AddressesStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def upsert_for_patient(self, patient_id: int, address: Address) -> None:
        self.conn.execute(
            """
            INSERT INTO addresses (patient_id, line_1, line_2, town, postcode, country)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(patient_id) DO UPDATE SET
                line_1 = excluded.line_1,
                line_2 = excluded.line_2,
                town = excluded.town,
                postcode = excluded.postcode,
                country = excluded.country
            """,
            [
                patient_id,
                address.line_1,
                address.line_2,
                address.town,
                address.postcode,
                address.country,
            ],
        )

    def insert_for_patient(self, patient_id: int, address: Address) -> None:
        self.conn.execute(
            """
            INSERT INTO addresses (patient_id, line_1, line_2, town, postcode, country)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                patient_id,
                address.line_1,
                address.line_2,
                address.town,
                address.postcode,
                address.country,
            ],
        )

    def update_for_patient(self, patient_id: int, address: Address) -> None:
        self.conn.execute(
            """
            UPDATE addresses
            SET line_1 = ?,
                line_2 = ?,
                town = ?,
                postcode = ?,
                country = ?
            WHERE patient_id = ?
            """,
            [
                address.line_1,
                address.line_2,
                address.town,
                address.postcode,
                address.country,
                patient_id,
            ],
        )

    def get_for_patient(self, patient_id: int) -> Address | None:
        row = self.conn.execute(
            """
            SELECT line_1, line_2, town, postcode, country
            FROM addresses
            WHERE patient_id = ?
            """,
            [patient_id],
        ).fetchone()

        if not row:
            return None

        return Address(
            line_1=row[0],
            line_2=row[1],
            town=row[2],
            postcode=row[3],
            country=row[4],
        )
