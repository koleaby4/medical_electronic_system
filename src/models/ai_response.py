from datetime import datetime

from pydantic import BaseModel, Field


class AiResponse(BaseModel):
    id: int | None = Field(None, description="Primary key")
    request_id: int
    response_json: str
    created_at: datetime | None = Field(None, description="Timestamp of the response")
