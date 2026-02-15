from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.medical_check_template import MedicalCheckTemplate, MedicalCheckTemplateItem

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/medical_check_templates", include_in_schema=False)
async def medical_check_templates(
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse:
    all_templates = storage.medical_check_templates.list_medical_check_templates()
    active_templates = [t for t in all_templates if t.is_active]
    deactivated_templates = [t for t in all_templates if not t.is_active]
    return templates.TemplateResponse(
        request,
        "medical_check_templates.html",
        {
            "active_page": "admin",
            "active_templates": active_templates,
            "deactivated_types": deactivated_templates,
        },
    )


@router.get("/medical_check_templates/new", include_in_schema=False)
async def new_medical_check_template(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "upsert_medical_check_template.html",
        {"active_page": "admin"},
    )


@router.post("/medical_check_templates/new", include_in_schema=False, response_model=None)
async def save_medical_check_template(
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse | RedirectResponse:
    form = await request.form()

    check_name = form.get("check_name", "").strip()
    if not check_name:
        return templates.TemplateResponse(
            request,
            "upsert_medical_check_template.html",
            {
                "active_page": "admin",
                "error": "check_name is required",
            },
            status_code=400,
        )

    items_by_idx: dict[int, dict[str, Any]] = {}
    import re

    item_key_pattern = re.compile(r"^items\[(\d+)\]\[(name|units|input_type|placeholder)\]$")
    for key, value in form.multi_items():
        if m := item_key_pattern.match(key):
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

    raw_id = (form.get("template_id") or "").strip()
    template_id = int(raw_id) if raw_id.isdigit() else None

    if template_id is not None:
        existing = storage.medical_check_templates.get_template(template_id=template_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Template not found")

        # For editing, we only update the name and keep existing items
        items = existing.items

    storage.medical_check_templates.upsert(
        template_id=template_id,
        check_name=check_name,
        items=items,
    )

    return RedirectResponse(url="/admin/medical_check_templates", status_code=303)


@router.get("/medical_check_templates/{template_id}/edit", include_in_schema=False)
async def edit_medical_check_template(
    template_id: int,
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse:
    if mct := storage.medical_check_templates.get_template(template_id=template_id):
        return templates.TemplateResponse(
            request,
            "upsert_medical_check_template.html",
            {"active_page": "admin", "template": mct},
        )

    raise HTTPException(status_code=404, detail="Medical check template not found")


@router.post("/medical_check_templates/{template_id}/deactivate", include_in_schema=False)
async def deactivate_medical_check_template(
    template_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> RedirectResponse:
    storage.medical_check_templates.set_active_status(template_id=template_id, is_active=False)
    return RedirectResponse(url="/admin/medical_check_templates", status_code=303)


@router.post("/medical_check_templates/{template_id}/activate", include_in_schema=False)
async def activate_medical_check_template(
    template_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> RedirectResponse:
    storage.medical_check_templates.set_active_status(template_id=template_id, is_active=True)
    return RedirectResponse(url="/admin/medical_check_templates", status_code=303)


# JSON API: create a medical check template
@router.post("/medical_check_templates")
async def create_medical_check_template_json(
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> JSONResponse:
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
    template_id = storage.medical_check_templates.upsert(template_id=None, check_name=name, items=items)
    created = storage.medical_check_templates.get_template(template_id=template_id)
    headers = {"Location": f"/admin/medical_check_templates/{template_id}"}
    return JSONResponse(status_code=201, content=created.model_dump() if created else {}, headers=headers)


# JSON API: get a medical check template by id
@router.get("/medical_check_templates/{template_id}")
async def get_medical_check_template_json(
    template_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> MedicalCheckTemplate:
    if mct := storage.medical_check_templates.get_template(template_id=template_id):
        return mct

    raise HTTPException(status_code=404, detail="Medical check template not found")
