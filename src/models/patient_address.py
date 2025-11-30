from typing import Literal

from pydantic import BaseModel, field_validator


class Address(BaseModel):
    line_1: str
    line_2: str | None
    town: str
    postcode: str
    country: Literal["United Kingdom"] | str = "United Kingdom"


    @field_validator("postcode")
    def format_postcode(cls, v: str) -> str:
        v = v.strip().upper().replace(" ", "")
        if len(v) > 3:
            v = v[:-3] + " " + v[-3:]
        return v