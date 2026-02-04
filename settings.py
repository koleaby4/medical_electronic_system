import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings

load_dotenv()


class OpenAISettings(BaseModel):
    api_key: str
    prompt: str
    model: str
    url: str
    timeout: float


class Settings(BaseSettings):
    db_file: Path = Path(__file__).parent.absolute() / "database.sqlite"
    openai: OpenAISettings = OpenAISettings(
        api_key=os.getenv("openai_api_key") or os.getenv("OPENAI_API_KEY"),
        prompt=os.getenv("openai_prompt") or os.getenv("OPENAI_PROMPT"),
        model=os.getenv("openai_model") or os.getenv("OPENAI_MODEL"),
        url=os.getenv("openai_url") or os.getenv("OPENAI_URL"),
        timeout=float(os.getenv("openai_timeout")),
    )
