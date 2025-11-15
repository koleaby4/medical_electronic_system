from contextlib import suppress
from pathlib import Path
from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.models.patient import Patient


class DuckDbPatientsStorage(IPatientsStorage):
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.conn = duckdb.connect(self.db_file)

    def close(self) -> None:
        with suppress(Exception):
            self.conn.close()

    def create(self, patient: Patient) -> Patient:
        result = self.conn.execute(
            """
            INSERT INTO patients (
                title, 
                first_name,
                middle_name,
                last_name, 
                sex, 
                dob, 
                email, 
                phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING patient_id
            """,
            [
                patient.title.value,
                patient.first_name,
                patient.middle_name,
                patient.last_name,
                patient.sex,
                patient.dob,
                patient.email,
                patient.phone,
            ],
        ).fetchone()

        patient.patient_id = int(result[0]) if result else None
        return patient

    def get_all_patients(self) -> list[Patient]:
        with self.conn.cursor() as cur:
            cur.execute("select * from patients")
            return [Patient(**d) for d in _to_dicts(cur)]


def _to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
