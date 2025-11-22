from datetime import date

from pydantic import BaseModel, Field, field_validator
from src.models.enums import MedicalCheckType, MedicalCheckStatus
from src.models.medical_check_item import MedicalCheckItem


class MedicalCheck(BaseModel):
    check_id: int | None = Field(default=None, description="DB identifier")
    patient_id: int | None = Field(default=None, description="Patient identifier", exclude=True)
    check_date: date = Field(..., description="Date of the medical check")
    type: MedicalCheckType = Field(..., description="Type of medical check (e.g., blood, physicals, colonoscopy)")
    status: MedicalCheckStatus = Field(..., description="Clinical status of the check outcome (Red | Amber | Green)")
    notes: str | None = Field(None, description="Optional notes about the check")
    medical_check_items: list[MedicalCheckItem] = Field(default_factory=list)

    @field_validator("status", mode="before")
    @classmethod
    def convert_title(cls, v: str | MedicalCheckStatus) -> MedicalCheckStatus:
        return MedicalCheckStatus(v) if isinstance(v, str) else v


class MedicalChecks(BaseModel):
    records: list[MedicalCheck] = Field(default_factory=list)
