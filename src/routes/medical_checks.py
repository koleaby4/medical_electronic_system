import datetime
import json
import logging
from contextlib import suppress
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader

from src.data_access.db_storage import DbStorage
from src.dependencies import get_ai_service, get_storage
from src.models.enums import MedicalCheckStatus
from src.models.medical_check import MedicalCheck, MedicalChecks
from src.models.medical_check_item import MedicalCheckItem
from src.services.ai_service import AiService


logger = logging.getLogger(__name__)


def safe_json_decode(value: str) -> Any:
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


router = APIRouter()
templates = Jinja2Templates(directory="src/templates")
templates.env.add_extension("jinja2.ext.loopcontrols")
templates.env.filters["json_decode"] = safe_json_decode


def _read_attachment_content(file_path: Path) -> str | None:
    """Reads text content of an attachment if it is a text file or PDF."""
    if not file_path.exists() or not file_path.is_file():
        return None

    suffix = file_path.suffix.lower()

    # Handle PDF files
    if suffix == ".pdf":
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF attachment {file_path}: {e}")
            return None

    # Simple check for text files by extension
    text_extensions = {".txt", ".csv", ".json", ".xml", ".md"}
    if suffix not in text_extensions:
        return None

    try:
        # We assume UTF-8 for now.
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Error reading text attachment {file_path}: {e}")
        return None


# Todo: refactor this?
def _resolve_template_name(raw_name: str) -> str:
    """Resolve a user-submitted check template to a canonical string.

    - Maps common aliases to canonical strings: "physicals", "blood", "colonoscopy".
    - Otherwise, returns the trimmed input to support custom names.
    """
    key = (raw_name or "").strip()
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
async def list_medical_checks(
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> MedicalChecks:
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    checks = storage.medical_checks.get_medical_checks(patient_id)

    return MedicalChecks(records=checks)


async def _transcribe_recordings_task(check_id: int, storage: DbStorage, ai_service: AiService) -> None:
    """Background task to transcribe all voice recordings for a medical check."""
    recordings = storage.voice_recordings.get_recordings_by_check_id(check_id)
    for rec in recordings:
        if not rec.file_path:
            continue
        # file_path in DB is relative to voice_recordings/
        full_path = Path("voice_recordings") / rec.file_path
        if full_path.exists():
            transcript_json = await ai_service.transcribe_voice_recording(full_path)
            storage.voice_recordings.update_transcription(
                voice_recording_id=rec.voice_recording_id, full_text=transcript_json
            )


@router.post("", response_model=None)
async def create_medical_check(
    patient_id: int,
    request: Request,
    storage: Annotated[DbStorage, Depends(get_storage)],
    ai_service: Annotated[AiService, Depends(get_ai_service)],
    background_tasks: BackgroundTasks,
    check_type: Annotated[str, Form(alias="type")],
    check_date: Annotated[datetime.date, Form(alias="date")],
    status: Annotated[str, Form(...)],
    notes: Annotated[str | None, Form()] = None,
    param_count: Annotated[int | None, Form()] = None,
    attachments: list[UploadFile] = File(None),
    voice_recordings: list[UploadFile] = File(None),
) -> JSONResponse | RedirectResponse:
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
        try:
            items_payload = data.get("items") or []
            medical_check_items = [
                MedicalCheckItem(name=i.get("name"), units=i.get("units"), value=i.get("value")) for i in items_payload
            ]
            mc = MedicalCheck(
                patient_id=patient_id,
                check_date=data.get("observed_at") or data.get("check_date") or check_date,
                template_name=_resolve_template_name(str(data.get("type") or data.get("template_id") or check_type)),
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

        # Trigger AI analysis in background
        background_tasks.add_task(ai_service.prepare_and_send_request, patient_id)

        created = storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id)
        headers = {"Location": f"/patients/{patient_id}/medical_checks/{check_id}"}
        return JSONResponse(status_code=201, content=created.model_dump() if created else {}, headers=headers)

    # HTML form path (existing behavior)
    form = await request.form()
    medical_check_items_list: list[MedicalCheckItem] = []
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
        medical_check_items_list.append(
            MedicalCheckItem(
                name=str(name) if name else "",
                units=str(units) if units else "",
                value=str(value) if value else "",
            )
        )

    mc = MedicalCheck(
        patient_id=patient_id,
        check_date=check_date,
        template_name=_resolve_template_name(check_type),
        status=MedicalCheckStatus(status),
        notes=notes,
        medical_check_items=medical_check_items_list,
    )

    # Handle attachments
    processed_attachments = []
    if attachments:
        # directory structure: attachments/{iso-check-date}/{check_id}
        iso_date = mc.check_date.isoformat()
        # use a temporary structure or just save after creating the medical check
        # But wait, I need the check_id to create the directory.
        # So I'll create the check first, then save files, then update the check (or just add attachments to DB).
        pass

    check_id = storage.medical_checks.save(
        patient_id=patient_id,
        check_template=mc.template_name,
        check_date=mc.check_date,
        status=mc.status.value,
        medical_check_items=mc.medical_check_items,
        notes=mc.notes,
    )

    if attachments:
        # directory structure: attachments/{patient_id}/{iso-date}/{file_name}
        iso_date = mc.check_date.isoformat()
        upload_dir = Path("attachments") / str(patient_id) / iso_date
        upload_dir.mkdir(parents=True, exist_ok=True)

        for attachment in attachments:
            if not attachment.filename:
                continue

            file_path = upload_dir / attachment.filename
            content = await attachment.read()
            if not content:
                continue

            with open(file_path, "wb") as f:
                f.write(content)

            parsed_content = _read_attachment_content(file_path)

            db_file_path = f"{patient_id}/{iso_date}/{attachment.filename}"
            processed_attachments.append(
                {
                    "filename": attachment.filename,
                    "content_type": attachment.content_type,
                    "file_path": db_file_path,
                    "parsed_content": parsed_content,
                }
            )

        if processed_attachments:
            for att in processed_attachments:
                storage.medical_checks.conn.execute(
                    """
                    INSERT INTO medical_check_attachments (check_id, filename, content_type, file_path, parsed_content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        check_id,
                        att["filename"],
                        att["content_type"],
                        att["file_path"],
                        att.get("parsed_content"),
                    ],
                )
            storage.medical_checks.conn.commit()

    if voice_recordings:
        iso_date = mc.check_date.isoformat()
        upload_dir = Path("voice_recordings") / str(patient_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        for recording in voice_recordings:
            timestamp = datetime.datetime.now().strftime("%H%M%S_%f")
            filename = f"{iso_date}_{timestamp}.webm"
            file_path = upload_dir / filename

            content = await recording.read()
            if not content:
                continue

            with open(file_path, "wb") as f:
                f.write(content)

            db_file_path = f"{patient_id}/{filename}"
            storage.voice_recordings.insert_recording(check_id=check_id, file_path=db_file_path)

        storage.voice_recordings.conn.commit()
        # Trigger transcription in background
        background_tasks.add_task(_transcribe_recordings_task, check_id, storage, ai_service)

    # Trigger AI analysis in background
    background_tasks.add_task(ai_service.prepare_and_send_request, patient_id)

    return RedirectResponse(url=f"/patients/{patient.patient_id}?check_added=1", status_code=303)


@router.get("/new", include_in_schema=False)
async def new_medical_check(
    request: Request,
    patient_id: int,
    check_template_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse:
    """Generalized new medical check page based on medical check type items.

    Query param:
      - check_template_id: which type to use.
    """
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    selected_template = storage.medical_check_templates.get_template(template_id=check_template_id)
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
        request,
        "create_medical_check_generic.html",
        {
            "patient": patient,
            "check_template": selected_template.name,
            "parameters": parameters,
        },
    )


@router.get("/timeseries")
async def get_timeseries(
    patient_id: int,
    check_template: str,
    item_name: str,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> dict[str, Any]:
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
async def get_chartable_options(
    request: Request,
    patient_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse | dict[str, Any]:
    """
    Return list of chartable numeric options available for the patient.
    """
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    rows = storage.medical_checks.get_chartable_options(patient_id=patient_id)

    if request.headers.get("HX-Request"):
        if rows:
            options_html = "".join(
                [
                    f"<option value='{json.dumps({'type': r['check_template'], 'name': r['item_name']})}'>{r['label'] or (r['check_template'] + ' -> ' + r['item_name'])}</option>"
                    for r in rows
                ]
            )
            return HTMLResponse(content=options_html)
        else:
            return HTMLResponse(content='<option value="">No chartable data</option>')

    return {"records": rows}


# Details page or JSON depending on Accept header
@router.get("/{check_id}", include_in_schema=False, response_model=None)
async def medical_check_details(
    request: Request,
    patient_id: int,
    check_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> HTMLResponse | MedicalCheck:
    if not (patient := storage.patients.get_patient(patient_id=patient_id)):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    if mc := storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        if "application/json" in (request.headers.get("accept") or ""):
            return mc
        return templates.TemplateResponse(
            request,
            "medical_check_details.html",
            {
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
    status: Annotated[str, Form(...)],
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> RedirectResponse:
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
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> MedicalCheck:
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

    if updated := storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        return updated

    raise HTTPException(status_code=404, detail="Medical check not found after update")


@router.delete("/{check_id}")
async def delete_medical_check(
    patient_id: int,
    check_id: int,
    storage: Annotated[DbStorage, Depends(get_storage)],
) -> JSONResponse:
    if not storage.patients.get_patient(patient_id=patient_id):
        raise HTTPException(status_code=404, detail=f"Patient with patient_id={patient_id} not found")

    if not storage.medical_checks.get_medical_check(patient_id=patient_id, check_id=check_id):
        return JSONResponse(status_code=204, content=None)

    storage.medical_checks.delete(check_id=check_id)
    return JSONResponse(status_code=204, content=None)


@router.get("/attachments/{p_id}/{date_str}/{filename}", include_in_schema=False)
async def get_attachment(
    p_id: str,
    date_str: str,
    filename: str,
) -> FileResponse:
    file_path = Path("attachments") / p_id / date_str / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(file_path)
