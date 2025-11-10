# Setup

1. cd into the project folder
2. run ``.\setup.bat``

# Run app

* `.venv\Scripts\activate`
* `uv run python -m src.db_migrations.setup_duckdb`
* for dev -> `uv run uvicorn src.main:app --reload`
* for prod -> `uvicorn src.main:app`
* open browser to `http://localhost:8000`