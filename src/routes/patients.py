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
    format: str = "html",  # Optional legacy param: ?format=json for API
):
    patients = storage.patients.get_all_patients()

    # Prefer Accept header, keep query param for convenience
    if format.lower() == "json" or "application/json" in (request.headers.get("accept") or ""):
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
    # Content negotiation: JSON body for API, form data for HTML
    if is_json := "application/json" in (request.headers.get("content-type") or ""):
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

    # For API: return JSON with 201 and Location header
    if is_json:
        response = saved_patient
        # FastAPI will include response_model; set Location via header using RedirectResponse pattern is not ideal here
        return response
    # For HTML form: redirect to details
    return RedirectResponse(url=f"/patients/{saved_patient.patient_id}", status_code=303)

@router.put("/{patient_id}")
async def update_patient(
    request: Request,
    patient_id: int,
    storage: DbStorage = Depends(get_storage),
    title: str = Form(None),
    first_name: str = Form(None),
    middle_name: str | None = Form(None),
    last_name: str = Form(None),
    sex: str = Form(None),
    dob: date = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with id {patient_id} not found")

    is_json = "application/json" in (request.headers.get("content-type") or "")
    if is_json:
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
        # Create patient with the provided ID
        patient = Patient(patient_id=patient_id, **patient_data)
        saved_patient = storage.patients.save(patient)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return JSON for API or redirect for form submissions
    if is_json or "application/json" in (request.headers.get("accept") or ""):
        return saved_patient
    return RedirectResponse(url=f"/patients/{saved_patient.patient_id}", status_code=303)


# Transitional support for HTML forms posting with method override used by existing template/tests
@router.post("/{patient_id}", include_in_schema=False)
async def update_patient_post_method_override(
    request: Request,
    patient_id: int,
    storage: DbStorage = Depends(get_storage),
):
    form = await request.form()
    if form.get("_method") != "PUT":
        raise HTTPException(status_code=405, detail="Method Not Allowed")

    return await update_patient(
        request=request,
        patient_id=patient_id,
        storage=storage,
        title=form.get("title"),
        first_name=form.get("first_name"),
        middle_name=form.get("middle_name"),
        last_name=form.get("last_name"),
        sex=form.get("sex"),
        dob=form.get("dob"),
        email=form.get("email"),
        phone=form.get("phone"),
    )


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
    format: str = "html"  # Optional legacy param: ?format=json for API
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail="Patient not found")

    if format.lower() == "json" or "application/json" in (request.headers.get("accept") or ""):
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
