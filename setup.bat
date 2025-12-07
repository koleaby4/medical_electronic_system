@echo off

where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing uv...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
)

echo Syncing dependencies...
uv sync

echo.

echo Applying database migrations (Alembic upgrade head)...
uv run alembic upgrade head

echo.

echo.
echo Setup complete! Run: uv run uvicorn main:app --reload