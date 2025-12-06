from logging import getLogger
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = getLogger(__name__)
logger.setLevel("INFO")


def _find_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    for parent in [cur] + list(cur.parents):
        if (parent / "alembic.ini").exists() and (parent / "alembic").exists():
            return parent
    return Path.cwd()


def _make_alembic_config(db_path: str) -> Config:
    repo_root = _find_repo_root()
    cfg = Config(str(repo_root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    cfg.set_main_option("script_location", str(repo_root / "alembic"))
    return cfg


def create_tables(db: str):
    """Run Alembic migrations to create or upgrade the SQLite schema."""
    cfg = _make_alembic_config(db)
    logger.info("Applying Alembic migrations to %s", db)
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    create_tables("database.sqlite")
