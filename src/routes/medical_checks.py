import datetime
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

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
            request,
            "create_medical_check_physicals.html",
            {
                "active_page": "patients",
                "patient": patient,
                "check_type": "physicals",
            },
        )
    raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")


@router.get("/{check_id}", include_in_schema=False)
async def medical_check_details(
    request: Request, patient_id: int, check_id: int, storage: DbStorage = Depends(get_storage)
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")
    row = storage.medical_checks.get_one(patient_id=patient_id, check_id=check_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Medical check with check_id={check_id} not found for patient {patient_id}")

    mc = MedicalCheck(
        check_id=row.get("check_id"),
        patient_id=row.get("patient_id"),
        date=row.get("check_date"),
        type=MedicalCheckType(row.get("check_type")),
        status=MedicalCheckStatus(row.get("status")),
        notes=row.get("notes"),
        results=row.get("results"),
    )
    return templates.TemplateResponse(
        request,
        "medical_check_details.html",
        {
            "active_page": "patients",
            "patient": patient,
            "check": mc,
        },
    )


@router.post("/{check_id}/status", include_in_schema=False)
async def update_medical_check_status(
    patient_id: int,
    check_id: int,
    status: str = Form(...),
    storage: DbStorage = Depends(get_storage),
):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")
    # Validate status using enum
    try:
        new_status = MedicalCheckStatus(status)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid status value")

    storage.medical_checks.update_status(check_id=check_id, status=new_status.value)
    return RedirectResponse(url=f"/patients/{patient_id}/details", status_code=303)
