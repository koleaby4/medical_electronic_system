from datetime import date

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.enums import Title, Sex
from src.models.patient import Patient
from src.models.medical_check import MedicalChecks

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", include_in_schema=False)
async def render_patients(request: Request, storage: DbStorage = Depends(get_storage)):
    return templates.TemplateResponse(
        "patients.html",
        {
            "request": request,
            "active_page": "patients",
            "patients": storage.patients.get_all_patients(),
        },
    )


@router.get("/new", include_in_schema=False)
async def create_patient_form(request: Request):
    return templates.TemplateResponse(
        "create_patient.html",
        {
            "request": request,
            "active_page": "new_patient",
            "title_options": list(Title.__members__.values()),
            "sex_options": list(Sex.__members__.values()),
        },
    )


@router.post("/", include_in_schema=False)
async def create_patient(
    storage: DbStorage = Depends(get_storage),
    title: str = Form(...),
    first_name: str = Form(...),
    middle_name: str | None = Form(None),
    last_name: str = Form(...),
    sex: str = Form(...),
    dob: date = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
):
    patient = Patient(
        title=title,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        sex=sex,
        dob=dob,
        email=email,
        phone=phone,
    )
    storage.patients.create(patient)
    return RedirectResponse(url="/patients", status_code=303)


def get_age(dob: date) -> int:
    today = date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


@router.get("/{patient_id}/details", include_in_schema=False)
async def patient_details(request: Request, patient_id: int, storage: DbStorage = Depends(get_storage)):
    if patient := storage.patients.get_patient(patient_id=patient_id):
        return templates.TemplateResponse(
            "patient_details.html",
            {
                "request": request,
                "active_page": "patients",
                "patient": patient,
                "age": get_age(patient.dob),
            },
        )
    raise HTTPException(status_code=404, detail=f"Patient with {patient_id=} not found")


@router.get("/{patient_id}/medical_checks", response_model=MedicalChecks)
async def patient_medical_checks(patient_id: int, storage: DbStorage = Depends(get_storage)) -> MedicalChecks:
    if storage.patients.get_patient(patient_id=patient_id):
        return MedicalChecks(records=[])

    raise HTTPException(status_code=404, detail=f"Patient with {patient_id=} not found")
