from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    duckdb_file: Path = Path(__file__).parent.absolute() / "database.duckdb"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
