from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

import duckdb
from src.data_access.patients import PatientsStorage
from src.data_access.medical_checks import MedicalChecksStorage


@dataclass
class DbStorage:
    def __init__(self, duckdb_file: Path) -> None:
        self._conn = duckdb.connect(str(duckdb_file))
        self.patients = PatientsStorage(self._conn)
        self.medical_checks = MedicalChecksStorage(self._conn)

    def close(self) -> None:
        with suppress(Exception):
            self.patients.close()
        with suppress(Exception):
            self.medical_checks.close()
        with suppress(Exception):
            self._conn.close()
