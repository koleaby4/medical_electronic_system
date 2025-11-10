from datetime import date

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.enums import Title
from src.models.patient import Patient

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
        },
    )


@router.post("/", include_in_schema=False)
async def create_patient(
    storage: DbStorage = Depends(get_storage),
    title: str = Form(...),
    first_name: str = Form(...),
    middle_name: str | None = Form(None),
    last_name: str = Form(...),
    dob: date = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
):
    patient = Patient(
        title=title,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        dob=dob,
        email=email,
        phone=phone,
    )
    storage.patients.create(patient)
    return RedirectResponse(url="/patients", status_code=303)
