from datetime import datetime

from pydantic import BaseModel


class AiResponse(BaseModel):
    id: int | None = None
    request_id: int
    response_json: str
    created_at: datetime | None = None
