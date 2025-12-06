from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/medical_check_templates", include_in_schema=False)
async def medical_check_templates(request: Request):
    return templates.TemplateResponse(
        "medical_check_templates.html",
        {"request": request, "active_page": "admin", "templates": []},
    )


@router.get("/medical_check_templates/new", include_in_schema=False)
async def new_medical_check_template(request: Request):
    return templates.TemplateResponse(
        "upsert_medical_check_template.html",
        {"request": request, "active_page": "admin"},
    )
