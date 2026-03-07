import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from settings import OpenAISettings
from src.data_access.db_storage import DbStorage
from src.models.medical_check_item import MedicalCheckItem
from src.services.ai_service import AiService


@pytest.fixture
def temp_attachments_dir():
    # Setup
    attachments_dir = Path("attachments")
    backup_dir = Path("attachments_backup")

    if attachments_dir.exists():
        shutil.move(str(attachments_dir), str(backup_dir))

    attachments_dir.mkdir(exist_ok=True)

    yield attachments_dir

    # Teardown
    shutil.rmtree(str(attachments_dir), ignore_errors=True)
    if backup_dir.exists():
        shutil.move(str(backup_dir), str(attachments_dir))


@pytest.mark.asyncio
async def test_ai_service_includes_attachment_content(migrated_db, create_patient, temp_attachments_dir):
    # Setup
    db = DbStorage(migrated_db)
    settings = OpenAISettings(
        api_key="test_key",
        system_prompt="Test prompt",
        model="test-model",
        url="https://example.com",
        timeout=30.0,
        response_format={"type": "json_object"},
    )

    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(
            {"choices": [{"message": {"content": "Test AI Response"}}]}
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        ai_service = AiService(db, settings)

        patient_id = create_patient()

        # Create a dummy attachment on disk
        # Path format in DB: {iso-date}/{check_id}/{filename}
        iso_date = "2024-01-01"
        check_id = 123
        filename = "test_lab_results.txt"

        rel_dir = Path(iso_date) / str(check_id)
        abs_dir = temp_attachments_dir / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        file_content = "Glucose: 5.5 mmol/L (Normal: 4.0-6.0)"
        file_path = abs_dir / filename
        file_path.write_text(file_content, encoding="utf-8")

        db_file_path = f"{iso_date}/{check_id}/{filename}"

        # Add a medical check with an attachment reference in DB
        # We need to manually add to medical_check_attachments since save() doesn't do it automatically if we call it this way
        # Wait, medical_checks.save() DOES take attachments argument.

        db.medical_checks.save(
            patient_id=patient_id,
            check_template="Blood Test",
            check_date=iso_date,
            status="Green",
            medical_check_items=[MedicalCheckItem(name="Glucose", value="5.5", units="mmol/L")],
            notes="See attached",
            attachments=[
                {
                    "filename": filename,
                    "content_type": "text/plain",
                    "file_path": db_file_path,
                    "parsed_content": file_content,
                }
            ],
        )

        # Execute
        ai_req, ai_resp = await ai_service.prepare_and_send_request(patient_id)

        # Verify
        payload = json.loads(ai_req.request_payload_json)
        user_content = json.loads(payload["messages"][1]["content"])

        medical_history = user_content["medical_history"]
        assert len(medical_history) == 1
        check = medical_history[0]
        assert len(check["attachments"]) == 1
        attachment = check["attachments"][0]
        assert attachment["filename"] == filename
        assert attachment["content"] == file_content

        # Verify non-text attachments (e.g. .bin) are NOT included
        bin_filename = "data.bin"
        bin_rel_path = f"{iso_date}/{check_id}/{bin_filename}"
        bin_abs_path = abs_dir / bin_filename
        bin_abs_path.write_bytes(b"\x00\x01\x02\x03 dummy binary content")

        db.medical_checks.conn.execute(
            "INSERT INTO medical_check_attachments (check_id, filename, content_type, file_path) VALUES (?, ?, ?, ?)",
            [check["check_id"], bin_filename, "application/octet-stream", bin_rel_path],
        )
        db.medical_checks.conn.commit()

        # Re-send request
        ai_req2, _ = await ai_service.prepare_and_send_request(patient_id)
        payload2 = json.loads(ai_req2.request_payload_json)
        user_content2 = json.loads(payload2["messages"][1]["content"])
        check2 = user_content2["medical_history"][0]

        bin_attachment = next(a for a in check2["attachments"] if a["filename"] == bin_filename)
        assert "content" not in bin_attachment
