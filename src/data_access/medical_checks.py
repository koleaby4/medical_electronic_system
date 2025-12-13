import sqlite3

from src.data_access.base import BaseStorage
from src.data_access.medical_check_items import MedicalCheckItemsStorage
from src.models.enums import MedicalCheckStatus
from src.models.medical_check import MedicalCheck
from src.models.medical_check_item import MedicalCheckItem


class MedicalChecksStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)
        self.items = MedicalCheckItemsStorage(conn)

    def save(
        self,
        *,
        patient_id: int,
        check_type: int | str,
        check_date,
        status: str,
        medical_check_items: list[MedicalCheckItem],
        notes: str | None = None,
    ) -> int:
        # Resolve check_type to type_id (PK from medical_check_types) if provided as a string
        check_type_id: int
        if isinstance(check_type, int):
            check_type_id = check_type
        else:
            cur_lookup = self.conn.execute(
                """
                SELECT type_id
                FROM medical_check_types
                WHERE name = ? COLLATE NOCASE
                """,
                [check_type],
            )

            if row := cur_lookup.fetchone():
                check_type_id = int(row[0])
            else:
                # Auto-insert missing medical_check_type for convenience
                cur_ins = self.conn.execute(
                    """
                    INSERT INTO medical_check_types (name)
                    VALUES (?)
                    """,
                    [check_type],
                )
                check_type_id = int(cur_ins.lastrowid)

        cur = self.conn.execute(
            """
            INSERT INTO medical_checks (patient_id, type_id, check_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            [patient_id, check_type_id, check_date, status, notes],
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
                SELECT mc.check_id,
                       mc.patient_id,
                       n.name AS check_type,
                       mc.check_date,
                       mc.status,
                       mc.notes
                FROM medical_checks mc
                JOIN medical_check_types n ON n.type_id = mc.type_id
                WHERE mc.patient_id = ?
                ORDER BY mc.check_date DESC, mc.check_id DESC
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
                type=r.get("check_type"),
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
                SELECT mc.check_id,
                       mc.patient_id,
                       n.name AS check_type,
                       mc.check_date,
                       mc.status,
                       mc.notes
                FROM medical_checks mc
                JOIN medical_check_types n ON n.type_id = mc.type_id
                WHERE mc.patient_id = ?
                  AND mc.check_id = ?
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
            type=r.get("check_type"),
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

    def update_notes(self, *, check_id: int, notes: str | None) -> None:
        self.conn.execute(
            "UPDATE medical_checks SET notes = ? WHERE check_id = ?",
            [notes, check_id],
        )
        self.conn.commit()

    def delete(self, *, check_id: int) -> None:
        # Ensure child rows are removed first due to FK constraints
        self.conn.execute("DELETE FROM medical_check_items WHERE check_id = ?", [check_id])
        self.conn.execute("DELETE FROM medical_checks WHERE check_id = ?", [check_id])
        self.conn.commit()

    def get_chartable_options(self, *, patient_id: int) -> list[dict]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT n.name AS check_type,
                       ti.name  item_name,
                       n.name || ' -> ' || ti.name  label
                FROM medical_check_types n
                JOIN medical_check_type_items ti
                      ON ti.type_id = n.type_id
                JOIN medical_checks mc
                      ON mc.type_id = n.type_id
                JOIN medical_check_items mci
                      ON mci.check_id = mc.check_id
                    AND mci.name = ti.name COLLATE NOCASE
                WHERE mc.patient_id = ?
                    AND LOWER(ti.input_type) = 'number'
                GROUP BY n.name, ti.name
                ORDER BY label COLLATE NOCASE
                """,
                [patient_id],
            )
            return self._fetch_all_dicts(cur)
        finally:
            cur.close()
