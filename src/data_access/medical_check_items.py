from contextlib import suppress
from pathlib import Path

import duckdb
from src.models.medical_check import MedicalCheckItem


class MedicalCheckItemsStorage:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.conn = duckdb.connect(self.db_file)

    def close(self) -> None:
        with suppress(Exception):
            self.conn.close()

    def insert_items(self, *, check_id: int, medical_check_items: list[MedicalCheckItem]) -> None:
        for mci in medical_check_items:
            self.conn.execute(
                """
                INSERT INTO medical_check_items (check_id, name, units, value)
                VALUES (?, ?, ?, ?)
                """,
                [check_id, mci.name, mci.units, str(mci.value)],
            )

    def get_items_by_check_id(self, *, check_id: int) -> list[MedicalCheckItem]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT check_item_id, name, units, value
                FROM medical_check_items
                WHERE check_id = ?
                ORDER BY check_item_id
                """,
                [check_id],
            )
            return [
                MedicalCheckItem(
                    check_item_id=str(check_item_id) if check_item_id else None,
                    name=name,
                    units=units or "",
                    value=value,
                )
                for (check_item_id, name, units, value) in cur.fetchall()
            ]


