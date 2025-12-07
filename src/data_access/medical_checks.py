import sqlite3

from src.data_access.base import BaseStorage
from src.data_access.medical_check_items import MedicalCheckItemsStorage
from src.models.enums import MedicalCheckType, MedicalCheckStatus
from src.models.medical_check import MedicalCheck
from src.models.medical_check_item import MedicalCheckItem


class MedicalChecksStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)
        self.items = MedicalCheckItemsStorage(conn)

    def close(self) -> None:
        return None

    def save(
        self,
        *,
        patient_id: int,
        check_type: str,
        check_date,
        status: str,
        medical_check_items: list[MedicalCheckItem],
        notes: str | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO medical_checks (patient_id, check_type, check_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            [patient_id, check_type, check_date, status, notes],
        )

        check_id = int(cur.lastrowid)

        self.items.insert_items(check_id=check_id, medical_check_items=medical_check_items)
        self.conn.commit()
        return check_id

    def get_medical_checks(self, patient_id: int) -> list[MedicalCheck]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT check_id, patient_id, check_type, check_date, status, notes
                FROM medical_checks
                WHERE patient_id = ?
                ORDER BY check_date DESC, check_id DESC
                """,
                [patient_id],
            )
            raw_rows = self._fetch_all_dicts(cur)
        finally:
            cur.close()

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
        cur = self.conn.cursor()
        try:
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
            r = self._fetch_one_dict(cur)
            if not r:
                return None
        finally:
            cur.close()

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
        self.conn.commit()

    def get_chartable_options(self, *, patient_id: int) -> list[dict]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT 
                    mc.check_type AS check_type,
                    ti.name AS item_name,
                    t.template_name || ' -> ' || ti.name AS label
                FROM medical_check_templates t
                JOIN medical_check_template_items ti 
                    ON ti.template_id = t.template_id
                JOIN medical_checks mc 
                    ON mc.check_type = t.template_name COLLATE NOCASE
                JOIN medical_check_items mci 
                    ON mci.check_id = mc.check_id
                   AND mci.name = ti.name COLLATE NOCASE
                WHERE mc.patient_id = ?
                  AND LOWER(ti.input_type) = 'number'
                GROUP BY mc.check_type, ti.name, t.template_name
                ORDER BY label COLLATE NOCASE
                """,
                [patient_id],
            )
            return self._fetch_all_dicts(cur)
        finally:
            cur.close()
