from pathlib import Path
from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.models.patient import Patient


class DuckDbPatientsStorage(IPatientsStorage):
    def __init__(self, duckdb_file: Path):
        self.duckdb_file = duckdb_file

    def create(self, patient: Patient) -> Patient:
        patient_dict = patient.model_dump()
        patient_dict["title"] = patient.title.value

        patient_dict["first_name"] = patient_dict["email"].lower()
        patient_dict["email"] = patient_dict["email"].lower()

        with duckdb.connect(self.duckdb_file) as conn:
            patient_id = conn.execute(
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

    def update(self, patient: Patient) -> None: ...

    def delete(self, patient_id: str) -> None: ...

    def get_patient(self, patient_id: int) -> Patient | None: ...

    def get_all_patients(self) -> list[Patient]:
        with duckdb.connect(self.duckdb_file).cursor() as cur:
            cur.execute("select * from patients")
            return [Patient(**d) for d in to_dicts(cur)]



def to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
