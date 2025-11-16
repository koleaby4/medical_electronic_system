import datetime
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.enums import MedicalCheckType, MedicalCheckStatus
from src.models.medical_check import MedicalCheck, MedicalChecks


router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("", response_model=MedicalChecks)
async def list_medical_checks(patient_id: int, storage: DbStorage = Depends(get_storage)) -> MedicalChecks:
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    rows = storage.medical_checks.list_by_patient(patient_id)
    records: list[MedicalCheck] = []
    for r in rows:
        records.append(
            MedicalCheck(
                check_id=r.get("check_id"),
                patient_id=r.get("patient_id"),
                date=r.get("check_date"),
                type=MedicalCheckType(r.get("check_type")),
                status=MedicalCheckStatus(r.get("status")),
                notes=r.get("notes"),
                results=r.get("results"),
            )
        )
    return MedicalChecks(records=records)


@router.post("", include_in_schema=False)
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

    form = await request.form()
    parameters: list[dict[str, Any]] = []
    if param_count is None:
        indices: set[int] = set()
        for k in form.keys():
            if k.startswith("param_name_") or k.startswith("param_value_") or k.startswith("param_units_"):
                try:
                    indices.add(int(k.split("_")[-1]))
                except Exception:
                    pass
    else:
        indices = set(range(int(param_count)))

    for i in sorted(indices):
        name = form.get(f"param_name_{i}")
        value = form.get(f"param_value_{i}")
        units = form.get(f"param_units_{i}")
        if name is None and value is None and units is None:
            continue
        parameters.append({"name": name or "", "units": units or "", "value": value})

    results: dict[str, Any] = {"parameters": parameters}
    if notes:
        results["notes"] = notes

    mc = MedicalCheck(
        patient_id=patient_id,
        date=date,
        type=type,
        status=status,
        notes=notes,
        results=results,
    )

    storage.medical_checks.create(
        patient_id=patient_id,
        check_type=mc.type.value,
        check_date=mc.check_date,
        status=mc.status.value,
        results=mc.results or {},
        notes=mc.notes,
    )

    return RedirectResponse(url=f"/patients/{patient.patient_id}/details", status_code=303)


@router.get("/physicals/new", include_in_schema=False)
async def new_physicals_check(request: Request, patient_id: int, storage: DbStorage = Depends(get_storage)):
    if patient := storage.patients.get_patient(patient_id=patient_id):
        return templates.TemplateResponse(
            "check_physicals_new.html",
            {
                "request": request,
                "active_page": "patients",
                "patient": patient,
                "check_type": "physicals",
            },
        )
    raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")
