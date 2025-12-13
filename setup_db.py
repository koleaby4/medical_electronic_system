from pathlib import Path

from src.db_migrations.setup import apply_migrations


def create_tables(db: str) -> None:
    """Apply project migrations to the given SQLite database file.

    This replaces the previous Alembic-based setup with a lightweight
    file-based migration runner tailored for SQLite.
    """
    apply_migrations(db)


if __name__ == "__main__":
    create_tables("database.sqlite")
