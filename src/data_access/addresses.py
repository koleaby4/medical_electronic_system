from __future__ import annotations

import duckdb

from src.models.address import Address


class AddressesStorage:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def upsert_for_patient(self, patient_id: int, address: Address) -> None:
        # Try to update first
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

        exists = self.conn.execute(
            "SELECT 1 FROM addresses WHERE patient_id = ?",
            [patient_id],
        ).fetchone()
        if not exists:
            self.insert_for_patient(patient_id, address)

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
