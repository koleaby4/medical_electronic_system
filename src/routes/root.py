from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", include_in_schema=False)
async def landing_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {})
