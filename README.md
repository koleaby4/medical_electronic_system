# Setup

1. cd into the project folder
2. run ``.\setup.bat``


# Test

tbc


# Run app

* `.venv\Scripts\activate`
* for dev -> `uv run uvicorn src.main:app --reload`
* for prod -> `uvicorn src.main:app`
* open browser to `http://localhost:8000`