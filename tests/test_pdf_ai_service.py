import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from settings import OpenAISettings
from src.data_access.db_storage import DbStorage
from src.services.ai_service import AiService


@pytest.mark.asyncio
async def test_ai_service_includes_pdf_content(migrated_db, create_patient, tmp_path):
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

    # Mock the attachments directory for AiService
    with patch("src.services.ai_service.Path"):
        # We need to be careful with patching Path because it's used inside AiService
        # and also in our test setup.
        pass

    # Alternative: use a real temporary directory and point AiService to it if possible.
    # AiService uses Path("attachments") / relative_path.
    # We can't easily change "attachments" root without modifying AiService.
    # Let's use the same approach as test_ai_service_attachments.py but for PDF.

    with patch("src.services.ai_service.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps({})
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        ai_service = AiService(db, settings)
        patient_id = create_patient()

        # Ensure attachments directory exists
        attachments_root = Path("attachments")
        attachments_root.mkdir(exist_ok=True)

        iso_date = "2024-01-01"
        patient_id = create_patient()
        pdf_filename = "test.pdf"
        rel_path = f"{patient_id}/{iso_date}/{pdf_filename}"
        abs_path = attachments_root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a real PDF with some text using pypdf if possible,
        # or just mock the extraction.
        # It's easier to mock the extraction for the test.

        with open(abs_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy")

        db.medical_checks.save(
            patient_id=patient_id,
            check_template="Lab Report",
            check_date=iso_date,
            status="Amber",
            medical_check_items=[],
            attachments=[
                {
                    "filename": pdf_filename,
                    "content_type": "application/pdf",
                    "file_path": rel_path,
                    "parsed_content": "Extracted PDF content in Markdown",
                }
            ],
        )

        with patch("src.services.ai_service.DocumentConverter") as mock_converter_class:
            mock_converter = mock_converter_class.return_value
            mock_result = MagicMock()
            mock_result.document.export_to_markdown.return_value = "Extracted PDF content in Markdown"
            mock_converter.convert.return_value = mock_result

            # Execute
            ai_req, _ = await ai_service.prepare_and_send_request(patient_id)

            # Verify
            payload = json.loads(ai_req.request_payload_json)
            user_content = json.loads(payload["messages"][1]["content"])
            attachment = user_content["medical_history"][0]["attachments"][0]

            assert attachment["filename"] == pdf_filename
            assert attachment["content"] == "Extracted PDF content in Markdown"

        # Cleanup
        if abs_path.exists():
            abs_path.unlink()
        try:
            abs_path.parent.rmdir()
            abs_path.parent.parent.rmdir()
        except OSError:
            pass
