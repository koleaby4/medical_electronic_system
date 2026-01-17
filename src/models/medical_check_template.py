from __future__ import annotations

from pydantic import BaseModel, Field


class MedicalCheckTemplateItem(BaseModel):
    name: str = Field("", description="Parameter name, e.g., height")
    units: str = Field("", description="Units for the parameter, e.g., cm")
    input_type: str = Field(
        "number",
        description="Input type (e.g., number | short_text )",
    )
    placeholder: str = Field("", description="Placeholder example value")


class MedicalCheckTemplate(BaseModel):
    """
    Represents a medical check type consisting of a name and a set of items.
    """

    template_id: int | None = Field(default=None, description="DB identifier (medical_check_templates.template_id)")
    name: str = Field(..., description="Human-readable check type name")
    is_active: bool = Field(default=True, description="Whether the template is active")
    items: list[MedicalCheckTemplateItem] = Field(default_factory=list)
