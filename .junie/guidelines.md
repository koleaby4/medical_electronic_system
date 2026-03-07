# Medical Electronic System Guidelines

This document outlines the coding conventions, project structure, and development practices for the Medical Electronic System project.

## Package Management

This project uses `uv` for package management. 

- To set up the project, run `.\setup.bat`.
- To install a new dependency: `uv add <package_name>`.
- To run the application: `uv run uvicorn src.main:app --reload`.
- To run tests: `uv run -m pytest`.

## Code Organization and Package Structure

The project follows a modular structure organized by functionality within the `src` directory:

- `src/main.py`: The entry point for the FastAPI application.
- `src/routes/`: Contains FastAPI router definitions for different entities (patients, medical checks, templates).
- `src/models/`: Pydantic models for data validation and representation.
- `src/data_access/`: Data access layer (Repository pattern) for interacting with the SQLite database.
- `src/services/`: Business logic layer, including integrations with external services like AI.
- `src/templates/`: Jinja2 templates for the HTMX-driven frontend.
- `src/static/`: Static assets such as CSS and SVG files.
- `src/db_migrations/`: SQLite database migration scripts.
- `tests/`: Automated tests using Pytest, including integration and coverage tests.

## Coding Conventions

### General Python Style

- Follow PEP 8 guidelines.
- Use `snake_case` for functions, methods, and variables.
- Use `PascalCase` for classes.
- Use `CAPITAL_SNAKE_CASE` for constants.
- Maintain a maximum line length of 120 characters (as configured in `pyproject.toml`).

### Type Hinting

- All functions and methods should include type hints for parameters and return types.
- Use Pydantic models for data validation and API request/response bodies.

### Linting and Formatting

- `ruff` is used for linting and code formatting.
- `mypy` is used for static type checking.
- Before committing, ensure the code passes linting and type checks.

### Database Interactions

- All database logic should reside in the `src/data_access/` directory.
- Use parameterized queries to prevent SQL injection.
- Migrations are handled via scripts in `src/db_migrations/`.

### Frontend Development

- The UI is built using FastAPI with Jinja2 templates and HTMX for interactivity.
- Templates should be modular and reused via `{% include %}` or `{% extend %}`.
- HTMX attributes should be used for dynamic content loading without full page refreshes.

### Testing

- Write tests for new features and bug fixes in the `tests/` directory.
- Aim for high test coverage, including both unit and integration tests.
- Use `pytest-asyncio` for testing asynchronous FastAPI endpoints.
