import sqlite3
from typing import Any

from src.data_access.addresses import AddressesStorage
from src.data_access.base import BaseStorage
from src.models.address import Address
from src.models.address_utils import build_address
from src.models.patient import Patient


class PatientsStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)
        self._addresses = AddressesStorage(conn)

    def save(self, patient: Patient) -> Patient:
        cur = self.conn.execute(
            """
            INSERT INTO patients (
                patient_id, title, first_name, middle_name, last_name,
                sex, dob, email, phone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(patient_id) DO UPDATE SET
                title = excluded.title,
                first_name = excluded.first_name,
                middle_name = excluded.middle_name,
                last_name = excluded.last_name,
                sex = excluded.sex,
                dob = excluded.dob,
                email = excluded.email,
                phone = excluded.phone
            """,
            [
                patient.patient_id,
                patient.title.value,
                patient.first_name,
                patient.middle_name,
                patient.last_name,
                patient.sex.value,
                patient.dob,
                patient.email,
                patient.phone,
            ],
        )

        if patient.patient_id is None:
            patient.patient_id = int(cur.lastrowid)

        self._addresses.upsert_for_patient(patient.patient_id, patient.address)
        self.conn.commit()
        return patient

    def get_all_patients(self) -> list[Patient]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.*, a.line_1, a.line_2, a.town, a.postcode, a.country
                FROM patients p
                LEFT JOIN addresses a ON a.patient_id = p.patient_id
                ORDER BY p.patient_id DESC
                """
            )
            return [_row_to_patient(r) for r in self._fetch_all_dicts(cur)]
        finally:
            cur.close()

    def get_patient(self, patient_id: int) -> Patient | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.*, a.line_1, a.line_2, a.town, a.postcode, a.country
                FROM patients p
                LEFT JOIN addresses a ON a.patient_id = p.patient_id
                WHERE p.patient_id = ?
                """,
                [patient_id],
            )
            if r := self._fetch_one_dict(cur):
                return _row_to_patient(r)
        finally:
            cur.close()


def _row_to_patient(r: dict[str, Any]) -> Patient:
    address = build_address(r)
    # Fallback for legacy rows without an address
    if address is None:
        address = Address(
            line_1="Unknown",
            line_2=None,
            town="Unknown",
            postcode="SW1A1AA",
            country="United Kingdom",
        )
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
