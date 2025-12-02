from pydantic import BaseModel, field_validator, Field


class Address(BaseModel):
    line_1: str
    line_2: str | None
    town: str
    postcode: str
    country: str = Field(default="United Kingdom")

    @field_validator("postcode")
    def format_postcode(cls, v: str) -> str:
        v = v.strip().upper().replace(" ", "")
        if len(v) > 3:
            v = v[:-3] + " " + v[-3:]
        return v

    @field_validator("country")
    def format_country(cls, v: str) -> str:
        return v.strip().title()
