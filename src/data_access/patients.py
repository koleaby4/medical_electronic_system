from typing import Any

import duckdb

from src.data_access.interfaces import IPatientsStorage
from src.models.patient import Patient
from src.models.address import Address


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

            if a := patient.address:
                self.conn.execute(
                    """
                    UPDATE addresses
                    SET line_1 = ?,
                        line_2 = ?,
                        town = ?,
                        postcode = ?,
                        country = ?
                    WHERE patient_id = ?
                    """,
                    [
                        a.line_1,
                        a.line_2,
                        a.town,
                        a.postcode,
                        a.country,
                        patient.patient_id,
                    ],
                )
                # Some DuckDB drivers may not report rowcount reliably; ensure a row exists, otherwise insert
                exists = self.conn.execute(
                    "SELECT 1 FROM addresses WHERE patient_id = ?",
                    [patient.patient_id],
                ).fetchone()
                if not exists:
                    self.conn.execute(
                        """
                        INSERT INTO addresses (patient_id, line_1, line_2, town, postcode, country)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            patient.patient_id,
                            a.line_1,
                            a.line_2,
                            a.town,
                            a.postcode,
                            a.country,
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

        if a := patient.address:

            self.conn.execute(
                """
                INSERT INTO addresses (patient_id, line_1, line_2, town, postcode, country)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    patient.patient_id,
                    a.line_1,
                    a.line_2,
                    a.town,
                    a.postcode,
                    a.country,
                ],
            )
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
            patients: list[Patient] = []
            for r in rows:
                address: Address | None = None
                if r.get("line_1") and r.get("town") and r.get("postcode"):
                    address = Address(
                        line_1=r.get("line_1"),
                        line_2=r.get("line_2"),
                        town=r.get("town"),
                        postcode=r.get("postcode"),
                        country=r.get("country") or "United Kingdom",
                    )
                patient_data = {k: v for k, v in r.items() if k in {
                    "patient_id", "title", "first_name", "middle_name", "last_name",
                    "sex", "dob", "email", "phone"
                }}
                patient = Patient(**patient_data, address=address)
                patients.append(patient)
            return patients

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
            r = rows[0]
            address: Address | None = None
            if r.get("line_1") and r.get("town") and r.get("postcode"):
                address = Address(
                    line_1=r.get("line_1"),
                    line_2=r.get("line_2"),
                    town=r.get("town"),
                    postcode=r.get("postcode"),
                    country=r.get("country") or "United Kingdom",
                )
            patient_data = {k: v for k, v in r.items() if k in {
                "patient_id", "title", "first_name", "middle_name", "last_name",
                "sex", "dob", "email", "phone"
            }}
            return Patient(**patient_data, address=address)


def _to_dicts(cur) -> list[dict[str, Any]]:
    cols: list[str] = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
