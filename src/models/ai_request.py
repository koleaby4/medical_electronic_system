from datetime import datetime

from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    id: int | None = Field(None, description="Primary key")
    patient_id: int
    model_name: str
    model_url: str
    system_prompt_text: str
    request_payload_json: str
    created_at: datetime | None = Field(None, description="Timestamp of the request")
