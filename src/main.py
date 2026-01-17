from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.routes import medical_check_templates, medical_checks, patients, root


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = Settings().db_file
    app.storage = storage = DbStorage(db_path)
    yield
    storage.close()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
    app.include_router(root.router)
    app.include_router(patients.router, prefix="/patients")
    app.include_router(medical_checks.router, prefix="/patients/{patient_id}/medical_checks")
    app.include_router(medical_check_templates.router, prefix="/admin")
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
