from typing import Protocol

from src.models.patient import Patient
from src.models.medical_check import MedicalCheck
from src.models.medical_check_item import MedicalCheckItem


class IPatientsStorage(Protocol):
    def create(self, patient: Patient) -> Patient: ...

    def get_patient(self, patient_id: int) -> Patient | None: ...

    def get_all_patients(self) -> list[Patient]: ...


class IMedicalCheckItemsStorage(Protocol):
    def insert_items(self, *, check_id: int, medical_check_items: list[MedicalCheckItem]) -> None: ...

    def get_items_by_check_id(self, *, check_id: int) -> list[MedicalCheckItem]: ...

    def get_time_series(self, *, patient_id: int, check_type: str, item_name: str) -> list[dict]: ...


class IMedicalChecksStorage(Protocol):
    items: IMedicalCheckItemsStorage

    def create(
        self,
        *,
        patient_id: int,
        check_type: str,
        check_date,
        status: str,
        medical_check_items: list[MedicalCheckItem],
        notes: str | None = None,
    ) -> int: ...

    def get_medical_checks(self, patient_id: int) -> list[MedicalCheck]: ...

    def get_medical_check(self, *, patient_id: int, check_id: int) -> MedicalCheck | None: ...

    def update_status(self, *, check_id: int, status: str) -> None: ...
