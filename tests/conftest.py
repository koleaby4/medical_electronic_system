from collections.abc import Generator
from pathlib import Path

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
