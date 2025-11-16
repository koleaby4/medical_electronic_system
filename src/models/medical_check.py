from datetime import date

from pydantic import BaseModel, Field
from src.models.enums import MedicalCheckType


class MedicalCheck(BaseModel):
    check_date: date = Field(
        ..., description="Date of the medical check", serialization_alias="date", validation_alias="date"
    )
    type: MedicalCheckType = Field(
        ..., description="Type of medical check (e.g., blood, physicals, colonoscopy)"
    )
    notes: str | None = Field(None, description="Optional notes about the check")


class MedicalChecks(BaseModel):
    records: list[MedicalCheck] = Field(default_factory=list)
