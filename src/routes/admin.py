import re
from typing import Any

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.medical_check_template import MedicalCheckTemplateItem

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/medical_check_templates", include_in_schema=False)
async def medical_check_templates(request: Request, storage: DbStorage = Depends(get_storage)):
    return templates.TemplateResponse(
        "medical_check_templates.html",
        {
            "request": request,
            "active_page": "admin",
            "templates": storage.medical_check_templates.list_medical_check_names(),
        },
    )


@router.get("/medical_check_templates/new", include_in_schema=False)
async def new_medical_check_template(request: Request):
    return templates.TemplateResponse(
        "upsert_medical_check_template.html",
        {"request": request, "active_page": "admin"},
    )


@router.post("/medical_check_templates/new", include_in_schema=False)
async def save_medical_check_template(request: Request, storage: DbStorage = Depends(get_storage)):
    form = await request.form()

    template_name = form.get("template_name", "").strip()
    if not template_name:
        return templates.TemplateResponse(
            "upsert_medical_check_template.html",
            {
                "request": request,
                "active_page": "admin",
                "error": "Template name is required",
            },
            status_code=400,
        )

    # Parse items like items[0][name], items[0][units], etc.
    items_by_idx: dict[int, dict[str, Any]] = {}
    pattern = re.compile(r"^items\[(\d+)\]\[(name|units|input_type|placeholder)\]$")
    for key, value in form.multi_items():
        m = pattern.match(key)
        if not m:
            continue
        idx = int(m.group(1))
        field = m.group(2)
        items_by_idx.setdefault(idx, {})[field] = (value or "").strip()

    items: list[MedicalCheckTemplateItem] = []
    for idx in items_by_idx:
        item = items_by_idx[idx]
        items.append(
            MedicalCheckTemplateItem(
                name=(item.get("name") or "").strip(),
                units=(item.get("units") or "").strip(),
                input_type=(item.get("input_type") or "number").strip(),
                placeholder=(item.get("placeholder") or "").strip(),
            )
        )

    # template_id is optional (for future edit use)
    raw_id = (form.get("template_id") or "").strip()
    template_id = int(raw_id) if raw_id.isdigit() else None

    storage.medical_check_templates.upsert(
        template_id=template_id,
        template_name=template_name,
        items=items,
    )

    return RedirectResponse(url="/admin/medical_check_templates", status_code=303)
