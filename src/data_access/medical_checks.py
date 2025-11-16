from contextlib import suppress
from pathlib import Path
from typing import Any

import duckdb
import json


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
        results: dict[str, Any] | list[Any],
        notes: str | None = None,
    ) -> int:
        res = self.conn.execute(
            """
            INSERT INTO medical_checks (patient_id, check_type, check_date, results, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING check_id
            """,
            [patient_id, check_type, check_date, json.dumps(results), status, notes],
        ).fetchone()
        return int(res[0]) if res else 0

    def list_by_patient(self, patient_id: int) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT check_id, patient_id, check_type, check_date, results, status, notes
                FROM medical_checks
                WHERE patient_id = ?
                ORDER BY check_date DESC, check_id DESC
                """,
                [patient_id],
            )
            cols: list[str] = [desc[0] for desc in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            for r in rows:
                try:
                    r["results"] = json.loads(r.get("results") or "{}")
                except Exception:
                    r["results"] = {}
            return rows

    def get_one(self, *, patient_id: int, check_id: int) -> dict[str, Any] | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT check_id, patient_id, check_type, check_date, results, status, notes
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
            try:
                r["results"] = json.loads(r.get("results") or "{}")
            except Exception:
                r["results"] = {}
            return r

    def update_status(self, *, check_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE medical_checks SET status = ? WHERE check_id = ?",
            [status, check_id],
        )
