from fastapi import Request

from src.data_access.db_storage import DbStorage


def get_storage(request: Request) -> DbStorage:
    return request.app.storage
