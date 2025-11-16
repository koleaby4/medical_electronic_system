from typing import Protocol

from src.models.patient import Patient


class IPatientsStorage(Protocol):
    def create(self, patient: Patient) -> Patient: ...

    def get_patient(self, patient_id: int) -> Patient | None: ...

    def get_all_patients(self) -> list[Patient]: ...
