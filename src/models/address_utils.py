from __future__ import annotations

from typing import Any, Mapping

from src.models.address import Address


def build_address(data: Mapping[str, Any] | None = None) -> Address | None:
    addr_obj = data.get("address", data or {})

    line_1 = addr_obj.get("line_1")
    town = addr_obj.get("town")
    postcode = addr_obj.get("postcode")

    if not (line_1 and town and postcode):
        return None

    return Address(
        line_1=line_1,
        line_2=addr_obj.get("line_2"),
        town=town,
        postcode=postcode,
        country=addr_obj.get("country"),
    )
