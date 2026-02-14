import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.dependencies import get_ai_service


@pytest.mark.asyncio
async def test_send_to_ai_button_and_response(client: TestClient, create_patient, app):
    # 1. Create a patient
    patient_id = create_patient()

    # 2. Check if the button and summary div are present on the patient details page
    resp = client.get(f"/patients/{patient_id}")
    assert resp.status_code == 200
    assert "Summarise" in resp.text
    assert "Summary" in resp.text
    assert 'id="medicalNotes"' in resp.text
    assert 'id="sendToAiBtn"' in resp.text

    # 3. Mock AiService and trigger the button click via AJAX
    mock_ai_service = MagicMock()
    mock_response = MagicMock()
    content_json = json.dumps(
        {
            "Findings": "Patient is doing well.\n- Blood pressure is normal.",
            "Outstanding tasks": "- Schedule follow-up blood test.",
        }
    )
    mock_response.response_json = json.dumps({"choices": [{"message": {"content": content_json}}]})
    mock_ai_service.prepare_and_send_request = AsyncMock(return_value=(MagicMock(), mock_response))

    # Override the dependency in the app
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    try:
        # Perform the POST request with Accept: application/json
        resp = client.post(f"/patients/{patient_id}/send_to_ai", headers={"Accept": "application/json"})

        # Check if ai_service was called
        mock_ai_service.prepare_and_send_request.assert_called_once_with(patient_id)

        # Check JSON response
        assert resp.status_code == 200
        data = resp.json()
        assert data["choices"][0]["message"]["content"] == content_json
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_send_to_ai_error_handling(client: TestClient, create_patient, app):
    patient_id = create_patient()

    mock_ai_service = MagicMock()
    mock_ai_service.prepare_and_send_request = AsyncMock(side_effect=Exception("AI Failure"))

    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    try:
        # Perform the POST request with Accept: application/json
        resp = client.post(f"/patients/{patient_id}/send_to_ai", headers={"Accept": "application/json"})

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "AI Failure"
    finally:
        app.dependency_overrides.clear()
