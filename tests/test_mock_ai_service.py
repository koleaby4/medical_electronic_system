import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from settings import OpenAISettings
from src.data_access.db_storage import DbStorage
from src.services.mock_ai_service import MockAiService


@pytest.mark.asyncio
async def test_mock_ai_service_record_and_playback(migrated_db, create_patient, tmp_path, monkeypatch):
    db = DbStorage(migrated_db)
    fixtures_dir = tmp_path / "fixtures"

    monkeypatch.setenv("AI_MOCK_MODE", "record")
    monkeypatch.setenv("AI_FIXTURES_DIR", str(fixtures_dir))

    settings = OpenAISettings(
        api_key="test_key", prompt="Test prompt", model="test-model", url="https://example.com", timeout=30.0
    )

    patient_id = create_patient()

    # 1. Test RECORD mode
    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(
            {"choices": [{"message": {"content": "Recorded Response"}}]}
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        ai_service = MockAiService(db, settings)
        await ai_service.prepare_and_send_request(patient_id)

        # Verify file was created
        files = list(fixtures_dir.glob("*.json"))
        assert len(files) == 1
        with open(files[0], "r") as f:
            data = json.load(f)
            assert data["choices"][0]["message"]["content"] == "Recorded Response"

    # 2. Test PLAYBACK mode
    monkeypatch.setenv("AI_MOCK_MODE", "playback")
    # Ensure no OpenAI calls are made
    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock()

        ai_service = MockAiService(db, settings)
        ai_req, ai_resp = await ai_service.prepare_and_send_request(patient_id)

        assert ai_resp is not None
        resp_data = json.loads(ai_resp.response_json)
        assert resp_data["choices"][0]["message"]["content"] == "Recorded Response"
        mock_client.chat.completions.create.assert_not_called()
