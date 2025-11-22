from contextlib import suppress
from pathlib import Path

import duckdb

from src.data_access.medical_check_items import MedicalCheckItemsStorage
from src.models.enums import MedicalCheckType, MedicalCheckStatus
from src.models.medical_check import MedicalCheckItem, MedicalCheck


class MedicalChecksStorage:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.conn = duckdb.connect(self.db_file)
        self.items = MedicalCheckItemsStorage(db_file)

    def close(self) -> None:
        with suppress(Exception):
            self.conn.close()
        with suppress(Exception):
            self.items.close()

    def create(
        self,
        *,
        patient_id: int,
        check_type: str,
        check_date,
        status: str,
        medical_check_items: list[MedicalCheckItem],
        notes: str | None = None,
    ) -> int:
        res = self.conn.execute(
            """
            INSERT INTO medical_checks (patient_id, check_type, check_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
            RETURNING check_id
            """,
            [patient_id, check_type, check_date, status, notes],
        ).fetchone()

        check_id = int(res[0])

        self.items.insert_items(check_id=check_id, medical_check_items=medical_check_items)
        return check_id

    def get_medical_checks(self, patient_id: int) -> list[MedicalCheck]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT check_id, patient_id, check_type, check_date, status, notes
                FROM medical_checks
                WHERE patient_id = ?
                ORDER BY check_date DESC, check_id DESC
                """,
                [patient_id],
            )
            cols: list[str] = [desc[0] for desc in cur.description]
            raw_rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        records: list[MedicalCheck] = []
        for r in raw_rows:
            check_id = r.get("check_id")
            items = self.items.get_items_by_check_id(check_id=check_id)
            mc = MedicalCheck(
                check_id=r.get("check_id"),
                patient_id=r.get("patient_id"),
                check_date=r.get("check_date"),
                type=MedicalCheckType(r.get("check_type")),
                status=MedicalCheckStatus(r.get("status")),
                notes=r.get("notes"),
                medical_check_items=items,
            )
            records.append(mc)

        return records

    def get_medical_check(self, *, patient_id: int, check_id: int) -> MedicalCheck | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT check_id, 
                       patient_id, 
                       check_type, 
                       check_date, 
                       status, 
                       notes
                FROM medical_checks
                WHERE patient_id = ? 
                  AND check_id = ?
                """,
                [patient_id, check_id],
            )
            desc = cur.description
            if not desc:
                return None
            cols: list[str] = [d[0] for d in desc]
            row = cur.fetchone()
            if not row:
                return None
            r = dict(zip(cols, row))

        items = self.items.get_items_by_check_id(check_id=check_id)

        mc = MedicalCheck(
            check_id=r.get("check_id"),
            patient_id=r.get("patient_id"),
            check_date=r.get("check_date"),
            type=MedicalCheckType(r.get("check_type")),
            status=MedicalCheckStatus(r.get("status")),
            notes=r.get("notes"),
            medical_check_items=items,
        )
        return mc

    def update_status(self, *, check_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE medical_checks SET status = ? WHERE check_id = ?",
            [status, check_id],
        )
