from collections.abc import Generator
from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from src.db_migrations.setup_duckdb import create_tables
from src.main import create_app


@pytest.fixture()
def temp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "test.duckdb"
    monkeypatch.setenv("DUCKDB_FILE", str(db_path))
    return db_path


@pytest.fixture()
def migrated_db(temp_db_path: Path) -> Path:
    create_tables(str(temp_db_path))
    return temp_db_path


@pytest.fixture()
def app(migrated_db: Path):
    return create_app()


@pytest.fixture()
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


# Test helpers / fixtures
@pytest.fixture()
def create_patient(client: TestClient):
    """Factory fixture to create a sample patient and return its id.

    Allows overriding any form fields by passing a dict.
    """

    def _create(form_overrides: dict | None = None) -> int:
        default_form = {
            "title": "Mr",
            "first_name": "john",
            "middle_name": "albert",
            "last_name": "doe",
            "sex": "male",
            "dob": "1990-01-02",
            "email": "JOHN.DOE@EXAMPLE.COM",
            "phone": "+1-555-0100",
        }
        form = {**default_form, **(form_overrides or {})}

        resp = client.post("/patients", data=form, follow_redirects=False)
        # Depending on FastAPI/TestClient version, this may be 303/307
        assert resp.status_code in (200, 303, 307)

        # Prefer Location header; fallback to URL if redirects were followed (status 200)
        location = resp.headers.get("location") or str(resp.url)
        m = re.search(r"/patients/(\d+)", location)
        assert m, f"Could not parse patient id from location: {location}"
        return int(m.group(1))

    return _create
