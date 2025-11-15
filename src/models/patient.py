from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator

from src.models.enums import Title, Sex


class Patient(BaseModel):
    title: Title
    first_name: str
    last_name: str
    sex: Sex
    dob: date
    email: str
    phone: str
    middle_name: str | None = None
    patient_id: Optional[int] = None

    @field_validator("first_name", "last_name", "middle_name", mode="before")
    @classmethod
    def capitalize(cls, v: str):
        if v is None:
            return v
        return v.capitalize()

    @field_validator("email", mode="before")
    @classmethod
    def lower_case(cls, v: str):
        if v is None:
            return v
        return v.lower()

    @field_validator("title", mode="before")
    @classmethod
    def convert_title(cls, v: str | Title) -> Title:
        return Title(v) if isinstance(v, str) else v

    @field_validator("sex", mode="before")
    @classmethod
    def convert_sex(cls, v: str | Sex) -> Sex:
        return Sex(v) if isinstance(v, str) else v
