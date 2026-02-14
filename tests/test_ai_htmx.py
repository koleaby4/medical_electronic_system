import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from src.dependencies import get_ai_service

@pytest.mark.asyncio
async def test_send_to_ai_htmx_partial(client: TestClient, create_patient, app):
    # 1. Create a patient
    patient_id = create_patient()

    # 2. Mock AiService
    mock_ai_service = MagicMock()
    mock_response = MagicMock()
    content_dict = {
        "Findings": "Everything looks good.",
        "Charts": ["Vitals.Blood Pressure"]
    }
    content_json = json.dumps(content_dict)
    mock_response.response_json = json.dumps({"choices": [{"message": {"content": content_json}}]})
    mock_ai_service.prepare_and_send_request = AsyncMock(return_value=(MagicMock(), mock_response))

    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    try:
        # 3. Request partial via HTMX
        resp = client.post(
            f"/patients/{patient_id}/send_to_ai", 
            headers={"HX-Request": "true"}
        )

        assert resp.status_code == 200
        html = resp.text
        
        # Verify partial content
        assert "Findings" in html
        assert "Everything looks good." in html
        # Verify chart trigger
        assert 'class="ai-charts-trigger"' in html
        assert 'Vitals.Blood Pressure' in html
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_send_to_ai_htmx_error(client: TestClient, create_patient, app):
    patient_id = create_patient()

    mock_ai_service = MagicMock()
    mock_ai_service.prepare_and_send_request = AsyncMock(side_effect=Exception("Connection lost"))

    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    try:
        resp = client.post(
            f"/patients/{patient_id}/send_to_ai", 
            headers={"HX-Request": "true"}
        )

        assert resp.status_code == 200
        assert "alert-danger" in resp.text
        assert "Connection lost" in resp.text
    finally:
        app.dependency_overrides.clear()
