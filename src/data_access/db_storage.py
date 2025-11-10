from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from src.data_access.patients import DuckDbPatientsStorage


@dataclass
class DbStorage:
    def __init__(self, duckdb_file: Path) -> None:
        self.patients = DuckDbPatientsStorage(duckdb_file)

    def close(self) -> None:
        with suppress(Exception):
            self.patients.close()
