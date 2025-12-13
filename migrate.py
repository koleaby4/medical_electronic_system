from __future__ import annotations

import importlib.util
import logging
import re
import sqlite3
import sys
from logging import getLogger
from pathlib import Path

from src.db_migrations.utils import with_logging

logger = getLogger(__name__)
logger.setLevel("INFO")


@with_logging
def set_version(conn: sqlite3.Connection, v: str) -> None:
    conn.execute("UPDATE schema_version SET version = ?", (v,))


def _ensure_schema_version(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version(
            version TEXT PRIMARY KEY
        );
        """
    )
    cur = conn.execute("SELECT COUNT(*) FROM schema_version")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO schema_version(version) VALUES ('0000')")


def _get_current_version(conn: sqlite3.Connection) -> str:
    return conn.execute("SELECT version FROM schema_version").fetchone()[0]


def _get_migration_files() -> list[Path]:
    db_migrations = Path(__file__).parent / "src" / "db_migrations"

    return sorted(
        [f for f in db_migrations.iterdir() if re.match(r"^\d{4}_.+\.py$", f.name)],
        key=lambda p: p.stem,
    )


def _module_from_path(path: Path):
    # Load as a standalone module; migrations may import 'src.db_migrations.utils'
    spec = importlib.util.spec_from_file_location(f"db_migrations.{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load migration module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def apply_migrations(db_path: str | Path, target_version: str | None = None) -> None:
    """Apply migrations to reach the target_version (or latest if None).

    - If current < target -> upgrade by calling each migration's upgrade(conn).
      We set schema_version to the module stem after each successful call.
    - If current > target -> downgrade by calling each migration's downgrade(conn)
      in reverse order, and we set schema_version to the previous stem (or '0000').
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        _ensure_schema_version(conn)
        current = _get_current_version(conn)

        files = _get_migration_files()
        versions = [p.stem for p in files]
        stem_to_path = {p.stem: p for p in files}

        target = versions[-1] if target_version in (None, "latest") else target_version

        if target != "0000" and target not in stem_to_path:
            raise ValueError(f"Unknown target_version '{target}'. Available: {', '.join(versions) or 'none'} or '0000'")

        if current == target:
            return

        if current < target:
            versions_to_upgrade: list[str] = [s for s in versions if current < s <= target]
            for stem in versions_to_upgrade:
                module = _module_from_path(stem_to_path[stem])
                upgrade_fn = getattr(module, "upgrade", None)
                if not callable(upgrade_fn):
                    raise RuntimeError(f"Migration {stem}.py must define upgrade(conn)")
                with conn:
                    upgrade_fn(conn)
                    set_version(conn, stem)
        else:
            to_rollback: list[str] = [s for s in versions if target < s <= current]
            for stem in reversed(to_rollback):
                module = _module_from_path(stem_to_path[stem])
                downgrade_fn = getattr(module, "downgrade", None)
                if not callable(downgrade_fn):
                    raise RuntimeError(f"Migration {stem}.py must define downgrade(conn) for downgrades")
                with conn:
                    downgrade_fn(conn)
                    idx = versions.index(stem)
                    prev_stem = versions[idx - 1] if idx - 1 >= 0 else "0000"
                    set_version(conn, prev_stem)
    finally:
        conn.close()


if __name__ == "__main__":
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    db = Path(__file__).parent / "database.sqlite"
    target = sys.argv[1] if len(sys.argv) > 1 else None
    apply_migrations(db, target_version=target)
