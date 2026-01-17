from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_storage
from src.models.address import Address
from src.models.address_utils import build_address
from src.models.enums import Sex, Title
from src.models.patient import Patient

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("", include_in_schema=False)
async def list_patients(
    request: Request,
    storage: DbStorage = Depends(get_storage),
    format: str = "html"
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
        "upsert_patient.html",
        {
            "request": request,
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
            "upsert_patient.html",
            {
                "request": request,
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
    # Address fields (required, canonical names)
    line_1: str | None = Form(None),
    line_2: str | None = Form(None),
    town: str | None = Form(None),
    postcode: str | None = Form(None),
    country: str | None = Form(None),
):
    if is_json := "application/json" in (request.headers.get("content-type") or ""):
        data = await request.json()
        addr = build_address(data)
        if addr is None:
            raise HTTPException(status_code=400, detail="Address is required")

        patient_data = {
            "title": data.get("title"),
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "sex": data.get("sex"),
            "dob": data.get("dob"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "address": addr,
        }
    else:
        addr = build_address(
            {
                "line_1": line_1,
                "line_2": line_2,
                "town": town,
                "postcode": postcode,
                "country": country,
            }
        )
        # For legacy HTML form submissions, if address fields are omitted, fall back to a default address
        if addr is None:
            addr = Address(
                line_1="Unknown",
                line_2=None,
                town="Unknown",
                postcode="SW1A1AA",
                country=country or "United Kingdom",
            )
        patient_data = {
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "sex": sex,
            "dob": dob,
            "email": email,
            "phone": phone,
            "address": addr,
        }

    try:
        patient = Patient(**patient_data)
        saved_patient = storage.patients.save(patient)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if is_json:
        response = saved_patient
        return response

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
    # Address fields (canonical names)
    line_1: str | None = Form(None),
    line_2: str | None = Form(None),
    town: str | None = Form(None),
    postcode: str | None = Form(None),
    country: str | None = Form(None),
):
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with id {patient_id} not found")

    if is_json := "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
        addr = build_address(data)
        patient_data = {
            "title": data.get("title"),
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "sex": data.get("sex"),
            "dob": data.get("dob"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "address": addr,
        }
    else:
        addr = build_address(
            {
                "line_1": line_1,
                "line_2": line_2,
                "town": town,
                "postcode": postcode,
                "country": country,
            }
        )
        patient_data = {
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "sex": sex,
            "dob": dob,
            "email": email,
            "phone": phone,
            "address": addr,
        }

    try:
        if patient_data.get("address") is None:
            existing = storage.patients.get_patient(patient_id=patient_id)
            assert existing is not None
            patient_data["address"] = existing.address
        patient = Patient(patient_id=patient_id, **patient_data)
        saved_patient = storage.patients.save(patient)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if is_json or "application/json" in (request.headers.get("accept", "")):
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
        # Forward optional address fields explicitly so they are None/str, not Form(...) defaults
        line_1=form.get("line_1"),
        line_2=form.get("line_2"),
        town=form.get("town"),
        postcode=form.get("postcode"),
        country=form.get("country"),
    )


def _get_age(dob: date) -> int:
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
):
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail="Patient not found")

    # Serve JSON when requested via Accept header; otherwise render HTML template
    if "application/json" in request.headers.get("accept", ""):
        return patient

    return templates.TemplateResponse(
        "patient_details.html",
        {
            "request": request,
            "active_page": "patients",
            "patient": patient,
            "age": _get_age(patient.dob),
            # Provide available medical check types for UI dropdown
            "templates": storage.medical_check_types.list_medical_check_types(),
        },
    )
