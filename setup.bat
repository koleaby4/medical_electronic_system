@echo off

where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing uv...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
)

if not exist pyproject.toml (
    echo Initializing project with Python 3.13...
    uv init --python 3.13 --no-workspace
)

echo Syncing dependencies...
uv sync

echo.

if exist database.duckdb (
    echo 'database.duckdb' already exists
) else (
    uv run python src\db_migrations\setup_duckdb.py
    echo 'database.duckdb' created successfully
)

echo.

echo.
echo Setup complete! Run: uv run uvicorn main:app --reload