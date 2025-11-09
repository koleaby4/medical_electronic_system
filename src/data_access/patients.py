from pathlib import Path
from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.models.patient import Patient


class DuckDbPatientsStorage(IPatientsStorage):
    def __init__(self, duckdb_file: Path):
        self.duckdb_file = duckdb_file
        self.conn = duckdb.connect(self.duckdb_file)

    def create(self, patient: Patient) -> Patient:
        patient_dict = patient.model_dump()
        patient_dict["title"] = patient.title.value

        patient_dict["first_name"] = patient_dict["email"].lower()
        patient_dict["email"] = patient_dict["email"].lower()

        patient_id = self.conn.execute(
            """
            INSERT INTO patients (title, first_name, last_name, dob, email, phone, middle_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                patient.title,
                patient.first_name,
                patient.last_name,
                patient.dob,
                patient.email,
                patient.phone,
                patient.middle_name,
            ],
        ).fetchone()[0]

        patient.patient_id = patient_id

        return patient

    def get_all_patients(self) -> list[Patient]:
        with self.conn.cursor() as cur:
            cur.execute("select * from patients")
            return [Patient(**d) for d in _to_dicts(cur)]


def _to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
