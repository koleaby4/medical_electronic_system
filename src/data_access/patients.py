from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.models.patient import Patient


class PatientsStorage(IPatientsStorage):
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def close(self) -> None:
        return None

    def save(self, patient: Patient) -> Patient:
        if patient.patient_id:
            self.conn.execute(
                """
                UPDATE patients
                SET title       = ?,
                    first_name  = ?,
                    middle_name = ?,
                    last_name   = ?,
                    sex         = ?,
                    dob         = ?,
                    email       = ?,
                    phone       = ?
                WHERE patient_id = ?
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
                    patient.patient_id,
                ],
            )

            return patient

        result = self.conn.execute(
            """
            INSERT INTO patients (title, first_name, middle_name, last_name,
                                  sex, dob, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING patient_id
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

        patient.patient_id = int(result[0])
        return patient

    def get_all_patients(self) -> list[Patient]:
        with self.conn.cursor() as cur:
            cur.execute("""
                        SELECT *
                        FROM patients
                        ORDER BY patient_id DESC
                        """)
            return [Patient(**row) for row in _to_dicts(cur)]

    def get_patient(self, patient_id: int) -> Patient | None:
        with self.conn.cursor() as cur:
            cur.execute("select * from patients where patient_id = ?", [patient_id])
            rows = _to_dicts(cur)
            return Patient(**rows[0]) if rows else None


def _to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
