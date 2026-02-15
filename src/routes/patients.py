import json
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.data_access.db_storage import DbStorage
from src.dependencies import get_ai_service, get_storage
from src.models.address import Address
from src.models.address_utils import build_address
from src.models.enums import Sex, Title
from src.models.patient import Patient
from src.services.ai_service import AiService

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")
templates.env.filters["from_json"] = json.loads


@router.get("", include_in_schema=False)
async def list_patients(
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse:
    patients = storage.patients.get_all_patients()

    return templates.TemplateResponse(request, "patients.html", {"active_page": "patients", "patients": patients})


@router.get("/new", include_in_schema=False)
async def create_patient_form(request: Request) -> HTMLResponse:
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
async def edit_patient_form(
    request: Request,
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse:
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


@router.post("/{patient_id}/send_to_ai", response_model=None)
async def send_to_ai(
    request: Request,
    patient_id: int,
    ai_service: Annotated[AiService, Depends(get_ai_service)],
) -> HTMLResponse | JSONResponse | RedirectResponse | str:
    try:
        _, ai_resp = await ai_service.prepare_and_send_request(patient_id)

        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request,
                "_ai_summary.html",
                {
                    "ai_response": ai_resp.response_json if ai_resp else None,
                    "patient_id": patient_id,
                },
            )

        if "application/json" in (request.headers.get("accept") or ""):
            if ai_resp:
                return JSONResponse(content=json.loads(ai_resp.response_json))
            return JSONResponse(content={"error": "No response from AI"}, status_code=500)

        return RedirectResponse(url=f"/patients/{patient_id}?ai_success=1", status_code=303)
    except Exception as e:
        if request.headers.get("HX-Request"):
            return f'<div class="alert alert-danger">Error: {str(e)}</div>'

        if "application/json" in (request.headers.get("accept") or ""):
            return JSONResponse(content={"error": str(e)}, status_code=500)

        return RedirectResponse(url=f"/patients/{patient_id}?ai_error={str(e)}", status_code=303)


@router.post("", status_code=201, response_model=None)
async def create_patient(
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
    title: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    middle_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    sex: Annotated[str | None, Form()] = None,
    dob: Annotated[date | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
    line_1: Annotated[str | None, Form()] = None,
    line_2: Annotated[str | None, Form()] = None,
    town: Annotated[str | None, Form()] = None,
    postcode: Annotated[str | None, Form()] = None,
    country: Annotated[str | None, Form()] = None,
) -> RedirectResponse | Patient:
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


@router.put("/{patient_id}", response_model=None)
async def update_patient(
    request: Request,
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
    title: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    middle_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    sex: Annotated[str | None, Form()] = None,
    dob: Annotated[date | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
    line_1: Annotated[str | None, Form()] = None,
    line_2: Annotated[str | None, Form()] = None,
    town: Annotated[str | None, Form()] = None,
    postcode: Annotated[str | None, Form()] = None,
    country: Annotated[str | None, Form()] = None,
) -> RedirectResponse | Patient:
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
@router.post("/{patient_id}", include_in_schema=False, response_model=None)
async def update_patient_post_method_override(
    request: Request,
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> RedirectResponse | Patient:
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


@router.get("/{patient_id}", include_in_schema=False, response_model=None)
async def get_patient(
    request: Request,
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse | Patient:
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail="Patient not found")

    # Serve JSON when requested via Accept header; otherwise render HTML template
    if "application/json" in request.headers.get("accept", ""):
        return patient

    # Provide available medical check types for UI dropdown
    check_templates = [t for t in storage.medical_check_templates.list_medical_check_templates() if t.is_active]

    medical_checks = storage.medical_checks.get_medical_checks(patient_id)

    # Fetch last AI response if any
    last_ai_response = None
    if ai_requests := storage.ai_requests.get_by_patient(patient_id):
        last_request = ai_requests[0]
        if ai_responses := storage.ai_responses.get_by_request(last_request.id):
            last_ai_response = ai_responses[0].response_json

    return templates.TemplateResponse(
        request,
        "patient_details.html",
        {
            "active_page": "patients",
            "patient": patient,
            "age": _get_age(patient.dob),
            "templates": check_templates,
            "medical_checks": medical_checks,
            "last_ai_response": last_ai_response,
            "patient_id": patient_id,
        },
    )
