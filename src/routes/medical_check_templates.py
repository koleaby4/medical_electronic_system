import re
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.medical_check_template import MedicalCheckTemplate, MedicalCheckTemplateItem

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/medical_check_templates", include_in_schema=False)
async def medical_check_templates(request: Request, storage: DbStorage = Depends(get_storage)):
    return templates.TemplateResponse(
        "medical_check_templates.html",
        {
            "request": request,
            "active_page": "admin",
            "types": storage.medical_check_templates.list_medical_check_templates(),
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

    check_name = form.get("check_name", "").strip()
    if not check_name:
        return templates.TemplateResponse(
            "upsert_medical_check_template.html",
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
        check_name=check_name,
        items=items,
    )

    return RedirectResponse(url="/admin/medical_check_templates", status_code=303)


@router.get("/medical_check_templates/{type_id}/edit", include_in_schema=False)
async def edit_medical_check_template(type_id: int, request: Request, storage: DbStorage = Depends(get_storage)):
    if mct := storage.medical_check_templates.get_check_type(type_id=type_id):
        return templates.TemplateResponse(
            "upsert_medical_check_template.html",
            {"request": request, "active_page": "admin", "template": mct},
        )

    raise HTTPException(status_code=404, detail="Medical check template not found")


# JSON API: create a medical check template
@router.post("/medical_check_templates")
async def create_medical_check_template_json(request: Request, storage: DbStorage = Depends(get_storage)):
    if "application/json" not in (request.headers.get("content-type") or ""):
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    data = await request.json()
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Field 'name' is required")

    items_payload = data.get("items") or []
    items: list[MedicalCheckTemplateItem] = []
    for i in items_payload:
        items.append(
            MedicalCheckTemplateItem(
                name=(i.get("name") or "").strip(),
                units=(i.get("units") or "").strip(),
                input_type=(i.get("input_type") or "number").strip(),
                placeholder=(i.get("placeholder") or "").strip(),
            )
        )
    type_id = storage.medical_check_templates.upsert(template_id=None, check_name=name, items=items)
    created = storage.medical_check_templates.get_check_type(type_id=type_id)
    headers = {"Location": f"/admin/medical_check_templates/{type_id}"}
    return JSONResponse(status_code=201, content=created.model_dump() if created else {}, headers=headers)


# JSON API: get a medical check template by id
@router.get("/medical_check_templates/{type_id}")
async def get_medical_check_template_json(type_id: int, storage: DbStorage = Depends(get_storage)) -> MedicalCheckTemplate:
    mct = storage.medical_check_templates.get_check_type(type_id=type_id)
    if not mct:
        raise HTTPException(status_code=404, detail="Medical check template not found")
    return mct


# JSON API: update a medical check template (replace items)
@router.put("/medical_check_templates/{type_id}")
async def update_medical_check_template_json(type_id: int, request: Request, storage: DbStorage = Depends(get_storage)):
    if "application/json" not in (request.headers.get("content-type") or ""):
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    if not storage.medical_check_templates.get_check_type(type_id=type_id):
        raise HTTPException(status_code=404, detail="Medical check template not found")

    data = await request.json()
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Field 'name' is required")

    items_payload = data.get("items", [])
    items: list[MedicalCheckTemplateItem] = []

    for i in items_payload:
        items.append(
            MedicalCheckTemplateItem(
                name=(i.get("name") or "").strip(),
                units=(i.get("units") or "").strip(),
                input_type=(i.get("input_type") or "number").strip(),
                placeholder=(i.get("placeholder") or "").strip(),
            )
        )
    storage.medical_check_templates.upsert(template_id=type_id, check_name=name, items=items)
    updated = storage.medical_check_templates.get_check_type(type_id=type_id)
    return updated


# JSON API: delete a medical check template
@router.delete("/medical_check_templates/{type_id}")
async def delete_medical_check_template_json(type_id: int, storage: DbStorage = Depends(get_storage)):
    if not storage.medical_check_templates.get_check_type(type_id=type_id):
        return JSONResponse(status_code=204, content=None)

    try:
        storage.medical_check_templates.delete(type_id=type_id)
    except sqlite3.IntegrityError:
        return JSONResponse(
            status_code=409,
            content={"detail": f"{type_id=} is in use by existing medical checks and cannot be deleted"}
        )
    return JSONResponse(status_code=204, content=None)
