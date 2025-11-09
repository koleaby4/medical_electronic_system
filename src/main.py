from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.routes import root, patients
import uvicorn


def create_app(storage: DbStorage) -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
    app.include_router(root.router)
    app.include_router(patients.router, prefix="/patients")

    app.storage = storage

    return app


app = create_app(DbStorage(Settings().duckdb_file))

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
