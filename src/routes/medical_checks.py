import datetime
from contextlib import suppress

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.enums import MedicalCheckStatus
from src.models.medical_check import MedicalCheck, MedicalChecks
from src.models.medical_check_item import MedicalCheckItem
from src.models.medical_check_template import MedicalCheckTemplate

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


# Todo: refactor this?
def _resolve_medical_check_template(raw: str) -> str:
    """Resolve a user-submitted check template to a canonical string.

    - Maps common aliases to canonical strings: "physicals", "blood", "colonoscopy".
    - Otherwise, returns the trimmed input to support custom names.
    """
    key = (raw or "").strip()
    key_lc = key.lower()
    # Normalize common separators for aliasing
    key_norm = key_lc.replace("_", " ").replace("-", " ")
    key_norm = " ".join(key_norm.split())

    # Simple aliasing to common built-ins
    if key_norm.startswith("physical") or key_norm == "physicals":
        return "physicals"
    if "blood" in key_norm:
        return "blood"
    if "colonoscopy" in key_norm:
        return "colonoscopy"

    # Fallback: accept custom name
    if key:
        return key
    raise HTTPException(status_code=400, detail="Check type is required")


@router.get("", response_model=MedicalChecks)
async def list_medical_checks(patient_id: int, storage: DbStorage = Depends(get_storage)) -> MedicalChecks:
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    checks: list[MedicalCheck] = storage.medical_checks.get_medical_checks(patient_id)
    return MedicalChecks(records=checks)


@router.post("")
async def create_medical_check(
    patient_id: int,
    request: Request,
    storage: DbStorage = Depends(get_storage),
    type: str = Form(...),
    date: datetime.date = Form(...),
    status: str = Form(...),
    notes: str | None = Form(None),
    param_count: int | None = Form(None),
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    # JSON submission path
    if "application/json" in (request.headers.get("content-type") or ""):
        data = await request.json()
        try:
            items_payload = data.get("items") or []
            medical_check_items = [
                MedicalCheckItem(name=i.get("name"), units=i.get("units"), value=i.get("value")) for i in items_payload
            ]
            mc = MedicalCheck(
                patient_id=patient_id,
                check_date=data.get("observed_at") or data.get("check_date") or date,
                template_name=_resolve_medical_check_template(str(data.get("type") or data.get("type_id") or type)),
                status=MedicalCheckStatus(str(data.get("status") or status)),
                notes=data.get("notes"),
                medical_check_items=medical_check_items,
            )
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid payload: {e}")

        check_id = storage.medical_checks.save(
            patient_id=patient_id,
            check_template=mc.template_name,
            check_date=mc.check_date,
            status=mc.status.value,
            medical_check_items=mc.medical_check_items,
            notes=mc.notes,
        )

        created = storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id)
        headers = {"Location": f"/patients/{patient_id}/medical_checks/{check_id}"}
        return JSONResponse(status_code=201, content=created.model_dump() if created else {}, headers=headers)

    # HTML form path (existing behavior)
    form = await request.form()
    medical_check_items: list[MedicalCheckItem] = []
    if param_count is None:
        indices: set[int] = set()
        for k in form.keys():
            if k.startswith("param_name_") or k.startswith("param_value_") or k.startswith("param_units_"):
                with suppress(Exception):
                    indices.add(int(k.split("_")[-1]))
    else:
        indices = set(range(int(param_count)))

    for i in sorted(indices):
        name = form.get(f"param_name_{i}")
        value = form.get(f"param_value_{i}")
        units = form.get(f"param_units_{i}")
        medical_check_items.append(MedicalCheckItem(name=name, units=units, value=value))

    mc = MedicalCheck(
        patient_id=patient_id,
        check_date=date,
        template_name=_resolve_medical_check_template(type),
        status=MedicalCheckStatus(status),
        notes=notes,
        medical_check_items=medical_check_items,
    )

    storage.medical_checks.save(
        patient_id=patient_id,
        check_template=mc.template_name,
        check_date=mc.check_date,
        status=mc.status.value,
        medical_check_items=mc.medical_check_items,
        notes=mc.notes,
    )

    return RedirectResponse(url=f"/patients/{patient.patient_id}", status_code=303)


@router.get("/new", include_in_schema=False)
async def new_medical_check(
    request: Request,
    patient_id: int,
    check_template_id: int | None = None,
    storage: DbStorage = Depends(get_storage),
):
    """Generalized new medical check page based on medical check type items.

    Query param:
      - check_template_id: which type to use; if not provided, the first type (by name) is used.
    """
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    available_templates: list[MedicalCheckTemplate] = storage.medical_check_templates.list_medical_check_templates()
    if not available_templates:
        raise HTTPException(status_code=404, detail="No medical check templates found")

    selected_template: MedicalCheckTemplate | None = None
    if check_template_id is not None:
        selected_template = storage.medical_check_templates.get_template(type_id=check_template_id)
    if selected_template is None:
        # fallback to first available
        selected_template = storage.medical_check_templates.get_template(type_id=available_templates[0].type_id)  # type: ignore[arg-type]

    if selected_template is None:
        raise HTTPException(status_code=404, detail="Selected medical check type not found")

    # Map type items to parameters expected by _medical_check_form.html
    def map_input_type(t: str) -> tuple[str, str | None, str | None]:
        t = (t or "").lower()
        if t == "number":
            # Allow integers and floats with up to 1 decimal
            return ("number", "0.1", r"^-?\d+(?:[\.,]\d)?$")

        # fallback to text
        return ("text", None, None)

    parameters = []
    for item in selected_template.items:
        html_type, step, pattern = map_input_type(item.input_type)
        parameters.append(
            {
                "name": item.name,
                "units": item.units,
                "input_type": html_type,
                "step": step or "",
                "pattern": pattern or "",
                "placeholder": item.placeholder,
            }
        )

    return templates.TemplateResponse(
        "create_medical_check_generic.html",
        {
            "request": request,
            "patient": patient,
            "check_template": selected_template.name,
            "parameters": parameters,
        },
    )


@router.get("/timeseries", response_model=None)
async def get_timeseries(
    patient_id: int,
    check_template: str,
    item_name: str,
    storage: DbStorage = Depends(get_storage),
):
    """Return item value over time for a given patient, check type and item name.
    Response example: {"records": [{"date": "2025-01-01", "value": "72.5", "units": "kg"}, ...]}
    """
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    series = storage.medical_checks.items.get_time_series(
        patient_id=patient_id, check_template=check_template, item_name=item_name
    )

    return {"records": series}


@router.get("/chartable_options", response_model=None)
async def get_chartable_options(patient_id: int, storage: DbStorage = Depends(get_storage)):
    """
    Return list of chartable numeric options available for the patient.
    Shape: {"records": [{"check_template": str, "item_name": str, "label": str}, ...]}
    """
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    rows = storage.medical_checks.get_chartable_options(patient_id=patient_id)
    return {"records": rows}


# Details page or JSON depending on Accept header
@router.get("/{check_id}", include_in_schema=False)
async def medical_check_details(
    request: Request, patient_id: int, check_id: int, storage: DbStorage = Depends(get_storage)
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    if mc := storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        if "application/json" in (request.headers.get("accept") or ""):
            return mc
        return templates.TemplateResponse(
            "medical_check_details.html",
            {
                "request": request,
                "active_page": "patients",
                "patient": patient,
                "check": mc,
            },
        )

    raise HTTPException(
        status_code=404, detail=f"Medical check with check_id={check_id} not found for patient {patient_id}"
    )


# Legacy form status update endpoint
@router.post("/{check_id}/status", include_in_schema=False)
async def update_medical_check_status(
    patient_id: int,
    check_id: int,
    status: str = Form(...),
    storage: DbStorage = Depends(get_storage),
):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    try:
        new_status = MedicalCheckStatus(status)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid status value")

    storage.medical_checks.update_status(check_id=check_id, status=new_status.value)
    return RedirectResponse(url=f"/patients/{patient_id}", status_code=303)


# JSON update endpoint for a medical check (status/notes for now)
@router.put("/{check_id}")
async def update_medical_check(
    request: Request,
    patient_id: int,
    check_id: int,
    storage: DbStorage = Depends(get_storage),
):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")
    if not storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        raise HTTPException(status_code=404, detail="Medical check not found")

    if "application/json" not in (request.headers.get("content-type") or ""):
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")

    data = await request.json()
    status_raw = data.get("status")
    notes = data.get("notes")

    if status_raw is not None:
        try:
            new_status = MedicalCheckStatus(status_raw)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid status value")
        storage.medical_checks.update_status(check_id=check_id, status=new_status.value)

    if "notes" in data:
        storage.medical_checks.update_notes(check_id=check_id, notes=notes)

    updated = storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id)
    return updated


@router.delete("/{check_id}")
async def delete_medical_check(patient_id: int, check_id: int, storage: DbStorage = Depends(get_storage)):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    if not storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        return JSONResponse(status_code=204, content=None)

    storage.medical_checks.delete(check_id=check_id)
    return JSONResponse(status_code=204, content=None)
