import sqlite3
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path

from src.data_access.ai_requests import AiRequestsStorage
from src.data_access.ai_responses import AiResponsesStorage
from src.data_access.medical_check_templates import MedicalCheckTemplatesStorage
from src.data_access.medical_checks import MedicalChecksStorage
from src.data_access.patients import PatientsStorage


# Register adapters for date and datetime to avoid DeprecationWarning in Python 3.12+
def adapt_date(val: date) -> str:
    return val.isoformat()


def adapt_datetime(val: datetime) -> str:
    return val.isoformat()


def convert_date(val: bytes) -> date:
    return date.fromisoformat(val.decode())


def convert_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())


sqlite3.register_adapter(date, adapt_date)
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("DATE", convert_date)
sqlite3.register_converter("DATETIME", convert_datetime)


class DbStorage:
    def __init__(self, db_file: Path) -> None:
        self._conn = sqlite3.connect(str(db_file), detect_types=sqlite3.PARSE_DECLTYPES)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self.patients = PatientsStorage(self._conn)
        self.medical_checks = MedicalChecksStorage(self._conn)
        self.medical_check_templates = MedicalCheckTemplatesStorage(self._conn)
        self.ai_requests = AiRequestsStorage(self._conn)
        self.ai_responses = AiResponsesStorage(self._conn)

    def close(self) -> None:
        with suppress(Exception):
            self._conn.close()
