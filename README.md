# Setup

1. cd into the project folder
2. run `.\setup.bat`
3. to populate DB with dummy patients -> `uv run python .\create_dummy_patients.py`

# Run app

* `.venv\Scripts\activate`
* for dev -> `uv run uvicorn src.main:app --reload`
* for prod -> `uvicorn src.main:app`
* open browser to `http://localhost:8000`

# Test

`uv run -m pytest`