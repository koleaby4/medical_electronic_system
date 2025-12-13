import re
from typing import Any

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.medical_check_type import MedicalCheckTypeItem

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/medical_check_types", include_in_schema=False)
async def medical_check_types(request: Request, storage: DbStorage = Depends(get_storage)):
    return templates.TemplateResponse(
        "medical_check_types.html",
        {
            "request": request,
            "active_page": "admin",
            "types": storage.medical_check_types.list_medical_check_types(),
        },
    )


@router.get("/medical_check_types/new", include_in_schema=False)
async def new_medical_check_type(request: Request):
    return templates.TemplateResponse(
        "upsert_medical_check_type.html",
        {"request": request, "active_page": "admin"},
    )


@router.post("/medical_check_types/new", include_in_schema=False)
async def save_medical_check_type(request: Request, storage: DbStorage = Depends(get_storage)):
    form = await request.form()

    template_name = form.get("template_name", "").strip()
    if not template_name:
        return templates.TemplateResponse(
            "upsert_medical_check_type.html",
            {
                "request": request,
                "active_page": "admin",
                "error": "Type name is required",
            },
            status_code=400,
        )

    # Parse items like items[0][name], items[0][units], etc.
    items_by_idx: dict[int, dict[str, Any]] = {}
    pattern = re.compile(r"^items\[(\d+)\]\[(name|units|input_type|placeholder)\]$")
    for key, value in form.multi_items():
        if m := pattern.match(key):
            idx = int(m.group(1))
            field = m.group(2)
            items_by_idx.setdefault(idx, {})[field] = (value or "").strip()

    items: list[MedicalCheckTypeItem] = []
    for idx in items_by_idx:
        item = items_by_idx[idx]
        items.append(
            MedicalCheckTypeItem(
                name=(item.get("name") or "").strip(),
                units=(item.get("units") or "").strip(),
                input_type=(item.get("input_type") or "number").strip(),
                placeholder=(item.get("placeholder") or "").strip(),
            )
        )

    # template_id is optional (for future edit use)
    raw_id = (form.get("template_id") or "").strip()
    template_id = int(raw_id) if raw_id.isdigit() else None

    storage.medical_check_types.upsert(
        template_id=template_id,
        template_name=template_name,
        items=items,
    )

    return RedirectResponse(url="/admin/medical_check_types", status_code=303)
