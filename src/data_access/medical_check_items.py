import sqlite3
from src.data_access.base import BaseStorage
from src.models.medical_check_item import MedicalCheckItem
import uuid


class MedicalCheckItemsStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def close(self) -> None:
        return None

    def insert_items(self, *, check_id: int, medical_check_items: list[MedicalCheckItem]) -> None:
        for mci in medical_check_items:
            check_item_id = mci.check_item_id or str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO medical_check_items (check_item_id, check_id, name, units, value)
                VALUES (?, ?, ?, ?, ?)
                """,
                [check_item_id, check_id, mci.name, mci.units or "", str(mci.value)],
            )

    def get_items_by_check_id(self, *, check_id: int) -> list[MedicalCheckItem]:
        cur = self.conn.cursor()
        try:
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
        finally:
            cur.close()

    def get_time_series(self, *, patient_id: int, check_type: str, item_name: str) -> list[dict]:
        """
        Return a time series for the given patient, check_type and item name.
        Each item: {date: YYYY-MM-DD, value: str, units: str}
        """
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT mc.check_date AS date, 
                    mci.value AS value, 
                    COALESCE(mci.units, '') AS units
                FROM medical_check_items mci
                    JOIN medical_checks mc
                ON mci.check_id = mc.check_id
                WHERE mc.patient_id = ?
                  AND mc.check_type = ?
                  AND mci.name = ?
                ORDER BY mc.check_date, mc.check_id, mci.check_item_id
                """,
                [patient_id, check_type, item_name],
            )
            return self._fetch_all_dicts(cur)
        finally:
            cur.close()
