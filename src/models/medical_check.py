from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator
from src.models.enums import MedicalCheckType, MedicalCheckStatus


class MedicalCheck(BaseModel):
    check_id: int | None = Field(default=None, description="DB identifier", exclude=True)
    patient_id: int | None = Field(default=None, description="Patient identifier", exclude=True)
    check_date: date = Field(
        ..., description="Date of the medical check", serialization_alias="date", validation_alias="date"
    )
    type: MedicalCheckType = Field(
        ..., description="Type of medical check (e.g., blood, physicals, colonoscopy)"
    )
    status: MedicalCheckStatus = Field(
        ..., description="Clinical status of the check outcome (Red | Amber | Green)"
    )
    notes: str | None = Field(None, description="Optional notes about the check")
    # Raw results payload as stored in DB; excluded from default API responses
    results: dict[str, Any] | list[Any] | None = Field(default=None, exclude=True)

    @field_validator("status", mode="before")
    @classmethod
    def convert_title(cls, v: str | MedicalCheckStatus) -> MedicalCheckStatus:
        return MedicalCheckStatus(v) if isinstance(v, str) else v



class MedicalChecks(BaseModel):
    records: list[MedicalCheck] = Field(default_factory=list)
