import os

from fastapi import Request

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.services.ai_service import AiService
from src.services.mock_ai_service import MockAiService


def get_storage(request: Request) -> DbStorage:
    return request.app.storage


def get_ai_service(request: Request) -> AiService:
    if os.getenv("AI_MOCK_MODE") in ("record", "playback"):
        return MockAiService(request.app.storage, Settings().openai)
    return AiService(request.app.storage, Settings().openai)
