from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.data_access.addresses import AddressesStorage
from src.models.patient import Patient
from src.models.address_utils import build_address


class PatientsStorage(IPatientsStorage):
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self._addresses = AddressesStorage(conn)

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

            if a := patient.address:
                self._addresses.upsert_for_patient(patient.patient_id, a)

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

        if a := patient.address:
            self._addresses.insert_for_patient(patient.patient_id, a)
        return patient

    def get_all_patients(self) -> list[Patient]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.*, a.line_1, a.line_2, a.town, a.postcode, a.country
                FROM patients p
                LEFT JOIN addresses a ON a.patient_id = p.patient_id
                ORDER BY p.patient_id DESC
                """
            )
            rows = _to_dicts(cur)
            return [_row_to_patient(r) for r in rows]

    def get_patient(self, patient_id: int) -> Patient | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.*, a.line_1, a.line_2, a.town, a.postcode, a.country
                FROM patients p
                LEFT JOIN addresses a ON a.patient_id = p.patient_id
                WHERE p.patient_id = ?
                """,
                [patient_id],
            )
            rows = _to_dicts(cur)
            if not rows:
                return None
            return _row_to_patient(rows[0])


def _to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _row_to_patient(r: dict[str, Any]) -> Patient:
    address = build_address(r)
    patient_data = {
        k: v
        for k, v in r.items()
        if k
        in {
            "patient_id",
            "title",
            "first_name",
            "middle_name",
            "last_name",
            "sex",
            "dob",
            "email",
            "phone",
        }
    }
    return Patient(**patient_data, address=address)
