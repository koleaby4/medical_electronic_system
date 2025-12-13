from datetime import date

from pydantic import BaseModel, Field

from src.models.enums import AllergyCategory, AllergySeverity, AllergyStatus


class Allergy(BaseModel):
    allergy_id: int | None = None
    allergen: str = Field(description="what patient is allergic to - e.g. penicillin, peanuts, dust mites")
    category: AllergyCategory = Field(description="category of the allergy - e.g. drug, food, environment, other")
    reaction: list[str] = Field(description="what reaction does the patient have - e.g. rash, anaphylaxis, hives")
    severity: AllergySeverity = Field(
        description="severity of the allergy - e.g. mild, moderate, severe, life-threatening"
    )
    status: AllergyStatus = Field(description="status of the allergy - e.g. active, inactive, resolved")
    onset_date: date | None = None
    notes: str | None = None
