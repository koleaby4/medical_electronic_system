from datetime import date

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.enums import Title, Sex
from src.models.patient import Patient

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("", include_in_schema=False)
async def list_patients(
    request: Request,
    storage: DbStorage = Depends(get_storage),
    format: str = "html",  # Optional: ?format=json for API
):
    patients = storage.patients.get_all_patients()

    if format.lower() == "json" or request.headers.get("accept") == "application/json":
        return patients

    return templates.TemplateResponse(
        "patients.html", {"request": request, "active_page": "patients", "patients": patients}
    )


@router.get("/new", include_in_schema=False)
async def create_patient_form(request: Request):
    return templates.TemplateResponse(
        request,
        "upsert_patient.html",
        {
            "active_page": "new_patient",
            "title_options": list(Title.__members__.values()),
            "sex_options": list(Sex.__members__.values()),
            "patient": None,
        },
    )


@router.get("/{patient_id}/edit", include_in_schema=False)
async def edit_patient_form(request: Request, patient_id: int, storage: DbStorage = Depends(get_storage)):
    if patient := storage.patients.get_patient(patient_id=patient_id):
        return templates.TemplateResponse(
            request,
            "upsert_patient.html",
            {
                "active_page": "patients",
                "title_options": list(Title.__members__.values()),
                "sex_options": list(Sex.__members__.values()),
                "patient": patient,
            },
        )
    raise HTTPException(status_code=404, detail=f"Patient with {patient_id=} not found")


async def _handle_patient_form(
    request: Request,
    storage: DbStorage,
    patient_id: int | None = None,
    title: str = Form(...),
    first_name: str = Form(...),
    middle_name: str | None = Form(None),
    last_name: str = Form(...),
    sex: str = Form(...),
    dob: date = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
):
    patient_data = {
        "title": title,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "sex": sex,
        "dob": dob,
        "email": email,
        "phone": phone,
    }

    # Create or update the patient
    patient = Patient(patient_id=patient_id, **patient_data)
    saved_patient = storage.patients.save(patient)

    # Redirect to patient details if updating, or to patients list if creating
    if patient_id:
        return RedirectResponse(url=f"/patients/{saved_patient.patient_id}", status_code=303)
    return RedirectResponse(url="/patients", status_code=303)


@router.post("", status_code=201, response_model=Patient)
async def create_patient(
    request: Request,
    storage: DbStorage = Depends(get_storage),
    # Form data
    title: str = Form(None),
    first_name: str = Form(None),
    middle_name: str | None = Form(None),
    last_name: str = Form(None),
    sex: str = Form(None),
    dob: date = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
):

    if is_json := "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
        patient_data = {
            "title": data.get("title"),
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "sex": data.get("sex"),
            "dob": data.get("dob"),
            "email": data.get("email"),
            "phone": data.get("phone"),
        }
    else:
        # Handle form submission
        patient_data = {
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "sex": sex,
            "dob": dob,
            "email": email,
            "phone": phone,
        }

    try:
        patient = Patient(**patient_data)
        saved_patient = storage.patients.save(patient)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return saved_patient if is_json else RedirectResponse(url=f"/patients/{saved_patient.patient_id}", status_code=303)

@router.put("/{patient_id}", include_in_schema=False)
@router.post("/{patient_id}", include_in_schema=False)
async def update_patient(
    request: Request,
    patient_id: int,
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
    # Check if it's a POST with _method=PUT (for browsers that don't support PUT)
    form_data = await request.form()
    if form_data.get("_method") == "PUT" or request.method == "PUT":
        return await _handle_patient_form(
            request=request,
            storage=storage,
            patient_id=patient_id,
            title=title,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            sex=sex,
            dob=dob,
            email=email,
            phone=phone,
        )
    raise HTTPException(status_code=405, detail="Method Not Allowed")


def get_age(dob: date) -> int:
    today = date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


@router.get("/{patient_id}", include_in_schema=False)
async def get_patient(
    request: Request,
    patient_id: int,
    storage: DbStorage = Depends(get_storage),
    format: str = "html"  # Optional: ?format=json for API
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail="Patient not found")

    if format.lower() == "json" or request.headers.get("accept") == "application/json":
        return patient

    return templates.TemplateResponse(
        "patient_details.html",
        {
            "request": request,
            "active_page": "patients",
            "patient": patient,
            "age": get_age(patient.dob),
        },
    )
