import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from settings import OpenAISettings
from src.data_access.db_storage import DbStorage
from src.models.medical_check_item import MedicalCheckItem
from src.services.ai_service import AiService


@pytest.mark.asyncio
async def test_ai_service_anonymization_and_storage(migrated_db, create_patient):
    # Setup
    db = DbStorage(migrated_db)
    settings = OpenAISettings(
        api_key="test_key", system_prompt="Test prompt", model="test-model", url="https://example.com", timeout=30.0
    )

    # Mock AsyncOpenAI.chat.completions.create
    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(
            {"choices": [{"message": {"content": "Test AI Response"}}]}
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        ai_service = AiService(db, settings)

        patient_id = create_patient(
            {"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "line_1": "123 Secret St"}
        )

        # Add a medical check
        db.medical_checks.save(
            patient_id=patient_id,
            check_template="Blood Test",
            check_date="2024-01-01",
            status="Green",
            medical_check_items=[MedicalCheckItem(name="Glucose", value="5.5", units="mmol/L")],
            notes="All good",
        )

        # Execute
        ai_req, ai_resp = await ai_service.prepare_and_send_request(patient_id)

        # Verify DB storage of request
        saved_requests = db.ai_requests.get_by_patient(patient_id)
        assert len(saved_requests) == 1
        assert saved_requests[0].id == ai_req.id

        # Verify DB storage of response
        saved_responses = db.ai_responses.get_by_request(ai_req.id)
        assert len(saved_responses) == 1
        assert json.loads(saved_responses[0].response_json)["choices"][0]["message"]["content"] == "Test AI Response"

        # Verify anonymization in payload
        payload = json.loads(saved_requests[0].request_payload_json)
        user_content = json.loads(payload["messages"][1]["content"])

        patient_info = user_content["patient_info"]
        assert "first_name" not in patient_info
        assert "last_name" not in patient_info
        assert "email" not in patient_info
        assert "address" not in patient_info

        assert patient_info["title"] == "Mr"
        assert patient_info["sex"] == "male"

        medical_history = user_content["medical_history"]
        assert len(medical_history) == 1
        assert medical_history[0]["template_name"] == "Blood Test"
        assert medical_history[0]["medical_check_items"][0]["name"] == "Glucose"

        # Verify OpenAI call
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "test-model"
        assert kwargs["messages"] == payload["messages"]
        assert kwargs["timeout"] == 30.0


@pytest.mark.asyncio
async def test_ai_service_no_api_key_still_saves_to_db(migrated_db, create_patient):
    # Setup
    db = DbStorage(migrated_db)
    settings = OpenAISettings(
        api_key="", system_prompt="Test prompt", model="test-model", url="https://example.com", timeout=30.0
    )
    ai_service = AiService(db, settings)

    patient_id = create_patient()

    # Mock AsyncOpenAI.chat.completions.create to ensure it's NOT called
    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock()

        # Execute
        ai_req, ai_resp = await ai_service.prepare_and_send_request(patient_id)

        # Verify DB storage
        saved_requests = db.ai_requests.get_by_patient(patient_id)
        assert len(saved_requests) == 1

        # Verify OpenAI call was NOT made
        mock_client.chat.completions.create.assert_not_called()
