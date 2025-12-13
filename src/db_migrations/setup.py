from __future__ import annotations

import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).parent


def _ensure_schema_version(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );
        """
    )
    cur = conn.execute("SELECT COUNT(*) FROM schema_version")
    if cur.fetchone()[0] == 0:
        # If database already has core tables, initialize to 1 (baseline applied), else 0
        cur2 = conn.execute(
            """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name IN (
                'patients','addresses','medical_checks','medical_check_items','medical_check_types','medical_check_type_items'
            );
            """
        )
        has_core = cur2.fetchone()[0] >= 3
        conn.execute("INSERT INTO schema_version(version) VALUES (?)", (1 if has_core else 0,))


def _get_current_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT version FROM schema_version").fetchone()[0])


def _set_version(conn: sqlite3.Connection, v: int) -> None:
    conn.execute("UPDATE schema_version SET version = ?", (v,))


def _iter_migrations():
    files = sorted(
        f for f in MIGRATIONS_DIR.iterdir() if f.suffix in {".sql", ".py"} and f.name[:4].isdigit()
    )
    for f in files:
        yield int(f.name[:4]), f


def apply_migrations(db_path: str | Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        _ensure_schema_version(conn)
        current = _get_current_version(conn)
        for ver, file in _iter_migrations():
            if ver <= current:
                continue
            if file.suffix == ".sql":
                sql = file.read_text(encoding="utf-8")
                with conn:
                    conn.executescript(sql)
                    _set_version(conn, ver)
            else:
                # Python migration files must define: def run(conn: sqlite3.Connection) -> None
                ns: dict = {}
                exec(file.read_text(encoding="utf-8"), ns)
                with conn:
                    ns["run"](conn)
                    _set_version(conn, ver)
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migrations(Path(__file__).resolve().parents[2] / "database.sqlite")
