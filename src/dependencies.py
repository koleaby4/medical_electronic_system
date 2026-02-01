from fastapi import Request

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.services.ai_service import AiService


def get_storage(request: Request) -> DbStorage:
    return request.app.storage


def get_ai_service(request: Request) -> AiService:
    return AiService(request.app.storage, Settings().openai)
