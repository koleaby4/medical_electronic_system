from contextlib import suppress
from pathlib import Path

import duckdb
from src.models.medical_check import MedicalCheckItem, MedicalCheck
from src.models.enums import MedicalCheckType, MedicalCheckStatus


class DuckDbMedicalChecksStorage:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.conn = duckdb.connect(self.db_file)

    def close(self) -> None:
        with suppress(Exception):
            self.conn.close()

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

        for mci in medical_check_items:
            self.conn.execute(
                """
                INSERT INTO medical_check_items (check_id, name, units, value)
                VALUES (?, ?, ?, ?)
                """,
                [check_id, mci.name, mci.units, str(mci.value)],
            )
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
            with self.conn.cursor() as cur2:
                cur2.execute(
                    """
                    SELECT check_item_id, name, units, value
                    FROM medical_check_items
                    WHERE check_id = ?
                    """,
                    [check_id],
                )
                items = [
                    MedicalCheckItem(
                        check_item_id=str(check_item_id),
                        name=name,
                        units=units or "",
                        value=value,
                    )
                    for (check_item_id, name, units, value) in cur2.fetchall()
                ]
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
                SELECT check_id, patient_id, check_type, check_date, status, notes
                FROM medical_checks
                WHERE patient_id = ? AND check_id = ?
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

        with self.conn.cursor() as cur2:
            cur2.execute(
                """
                SELECT check_item_id, name, units, value
                FROM medical_check_items
                WHERE check_id = ?
                ORDER BY check_item_id ASC
                """,
                [check_id],
            )
            items = [
                MedicalCheckItem(
                    check_item_id=str(check_item_id) if check_item_id else None,
                    name=name,
                    units=units or "",
                    value=value,
                )
                for (check_item_id, name, units, value) in cur2.fetchall()
            ]

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
