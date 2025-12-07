from __future__ import annotations

from pydantic import BaseModel, Field


class MedicalCheckTemplateItem(BaseModel):
    name: str = Field("", description="Parameter name, e.g., height")
    units: str = Field("", description="Units for the parameter, e.g., cm")
    input_type: str = Field(
        "short_text",
        description="Input type (e.g., number | short_text | long_text)",
    )
    placeholder: str = Field("", description="Placeholder example value")
    # Optional: when populated, defines the display order within the template
    sort_order: int | None = Field(default=None, description="Zero-based order in the template")


class MedicalCheckTemplate(BaseModel):
    """
    Represents a medical check template consisting of a name and a set of items.
    """

    template_id: int | None = Field(default=None, description="DB identifier")
    template_name: str = Field(..., description="Human-readable template name")
    items: list[MedicalCheckTemplateItem] = Field(default_factory=list)
