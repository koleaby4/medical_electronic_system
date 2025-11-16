from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from settings import Settings
from src.db_migrations.setup_duckdb import create_tables
from src.data_access.db_storage import DbStorage
from src.routes import root, patients, medical_checks
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = Settings().duckdb_file
    create_tables(str(db_path))
    app.storage = storage = DbStorage(db_path)
    yield
    storage.close()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
    app.include_router(root.router)
    app.include_router(patients.router, prefix="/patients")
    app.include_router(medical_checks.router, prefix="/patients/{patient_id}/medical_checks")
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
