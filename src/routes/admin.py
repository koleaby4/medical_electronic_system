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
