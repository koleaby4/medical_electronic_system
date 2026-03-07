import io
import json
from datetime import date
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import pytest
from src.services.ai_service import AiService
from settings import OpenAISettings, Settings
from src.data_access.db_storage import DbStorage
from pathlib import Path


@pytest.mark.asyncio
async def test_attachment_parsed_content_stored_and_used(client: TestClient):
    # 1. Create a sample patient
    patient_form = {
        "title": "Mr",
        "first_name": "Parsed",
        "last_name": "Test",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "parsed@example.com",
        "phone": "555-1234",
    }
    client.post("/patients", data=patient_form, follow_redirects=True)

    # Get patient ID
    patients_resp = client.get("/patients", headers={"Accept": "application/json"})
    patients = patients_resp.json()["records"]
    patient_id = patients[0]["patient_id"]

    # 2. Mock Docling/AiService to avoid real AI/PDF calls
    today = date.today().isoformat()
    check_form = {
        "type": "blood",
        "date": today,
        "status": "Green",
        "notes": "Testing parsed content storage",
        "param_count": "0",
    }

    file_content = b"This is a text file content."
    files = [("attachments", ("test.txt", io.BytesIO(file_content), "text/plain"))]

    # Patch _read_attachment_content in routes.medical_checks
    with patch("src.routes.medical_checks._read_attachment_content") as mock_read:
        mock_read.return_value = "PRE-PARSED CONTENT"

        resp = client.post(
            f"/patients/{patient_id}/medical_checks", data=check_form, files=files, follow_redirects=True
        )
        assert resp.status_code == 200
        mock_read.assert_called_once()

    # 3. Verify the parsed content is in the database
    checks_resp = client.get(f"/patients/{patient_id}/medical_checks", headers={"Accept": "application/json"})
    checks = checks_resp.json()["records"]
    check = checks[0]
    assert len(check["attachments"]) == 1
    attachment = check["attachments"][0]
    assert attachment["parsed_content"] == "PRE-PARSED CONTENT"

    # 4. Verify AI request uses the stored parsed content
    # Get the real test database path from Settings
    db_path = Path(Settings().db_file)
    db = DbStorage(db_path)
    try:
        settings = OpenAISettings(
            api_key="test",
            model="test",
            system_prompt="test prompt",
            url="http://test",
            timeout=30.0,
            response_format={"type": "json_object"},
        )
        ai_service = AiService(db, settings)

        with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = mock_openai_class.return_value
            mock_response = MagicMock()
            mock_response.model_dump_json.return_value = json.dumps({})
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            ai_service.client = mock_client

            await ai_service.prepare_and_send_request(patient_id)

            args, kwargs = mock_client.chat.completions.create.call_args
            user_message = kwargs["messages"][1]["content"]
            payload = json.loads(user_message)

            found_attachment = payload["medical_history"][0]["attachments"][0]
            assert found_attachment["filename"] == "test.txt"
            assert found_attachment["content"] == "PRE-PARSED CONTENT"
    finally:
        db.close()
