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
echo Setup complete! Run: uv run uvicorn main:app --reload