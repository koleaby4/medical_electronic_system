import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings

load_dotenv()


class OpenAISettings(BaseModel):
    api_key: str
    system_prompt: str
    model: str
    url: str
    timeout: float
    response_format: dict


class Settings(BaseSettings):
    db_file: Path = Path(__file__).parent.absolute() / "database.sqlite"
    openai: OpenAISettings = OpenAISettings(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        system_prompt=Path("system_prompt.txt").read_text(),
        model=os.getenv("OPENAI_MODEL", ""),
        url=os.getenv("OPENAI_URL", ""),
        timeout=float(os.getenv("OPENAI_TIMEOUT", "30.0")),
        response_format={"type": "json_object"},
    )
