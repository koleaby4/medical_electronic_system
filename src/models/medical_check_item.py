from typing import Any

from pydantic import BaseModel, Field


class MedicalCheckItem(BaseModel):
    check_item_id: str | None = Field(default=None, description="GUID of the item assigned by DB")
    name: str = Field("")
    units: str = Field("")
    value: Any = Field("")
