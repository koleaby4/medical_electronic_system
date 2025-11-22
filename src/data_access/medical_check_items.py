import duckdb
from src.models.medical_check_item import MedicalCheckItem


class MedicalCheckItemsStorage:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def close(self) -> None:
        return None

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

    def get_time_series(self, *, patient_id: int, check_type: str, item_name: str) -> list[dict]:
        """
        Return a time series for the given patient, check_type and item name.
        Each item: {date: YYYY-MM-DD, value: str, units: str}
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT mc.check_date AS date, 
                    mci.value AS value, 
                    COALESCE(mci.units, '') AS units
                FROM medical_check_items mci
                    JOIN medical_checks mc ON mci.check_id = mc.check_id
                WHERE mc.patient_id = ?
                  AND mc.check_type = ?
                  AND mci.name = ?
                ORDER BY mc.check_date, mc.check_id, mci.check_item_id
                """,
                [patient_id, check_type, item_name],
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
