from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from src.data_access.patients import PatientsStorage
from src.data_access.medical_checks import MedicalChecksStorage
from src.data_access.medical_check_types import MedicalCheckTypesStorage


@dataclass
class DbStorage:
    def __init__(self, db_file: Path) -> None:
        self._conn = sqlite3.connect(str(db_file))
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self.patients = PatientsStorage(self._conn)
        self.medical_checks = MedicalChecksStorage(self._conn)
        self.medical_check_types = MedicalCheckTypesStorage(self._conn)

    def close(self) -> None:
        with suppress(Exception):
            self.patients.close()
        with suppress(Exception):
            self.medical_checks.close()
        with suppress(Exception):
            self.medical_check_types.close()
        with suppress(Exception):
            self._conn.close()
