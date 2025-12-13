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
