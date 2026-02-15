from datetime import datetime

from pydantic import BaseModel


class AiRequest(BaseModel):
    id: int | None = None
    patient_id: int
    model_name: str
    model_url: str
    system_prompt_text: str
    request_payload_json: str
    created_at: datetime | None = None
