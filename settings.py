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


class Settings(BaseSettings):
    db_file: Path = Path(__file__).parent.absolute() / "database.sqlite"
    openai: OpenAISettings = OpenAISettings(
        api_key=os.getenv("OPENAI_API_KEY"),
        system_prompt=os.getenv("OPENAI_SYSTEM_PROMPT"),
        model=os.getenv("OPENAI_MODEL"),
        url=os.getenv("OPENAI_URL"),
        timeout=float(os.getenv("OPENAI_TIMEOUT")),
    )
