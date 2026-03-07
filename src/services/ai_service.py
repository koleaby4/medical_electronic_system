import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from pypdf import PdfReader

from settings import OpenAISettings
from src.data_access.db_storage import DbStorage
from src.models.ai_request import AiRequest
from src.models.ai_response import AiResponse
from src.models.medical_check import MedicalCheck
from src.models.patient import Patient


class AiService:
    def __init__(self, db: DbStorage, settings: OpenAISettings):
        self.db = db
        self.settings = settings
        self.client = (
            AsyncOpenAI(
                api_key=settings.api_key,
                base_url=settings.url.replace("/chat/completions", "") if settings.url else None,
            )
            if settings.api_key
            else None
        )

    async def prepare_and_send_request(self, patient_id: int) -> tuple[AiRequest, AiResponse | None]:
        # 1. Collect data
        patient = self.db.patients.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        medical_checks = self.db.medical_checks.get_medical_checks(patient_id)

        # 2. Anonymize data
        anonymized_patient = self._anonymize_patient(patient)
        anonymized_checks = [self._anonymize_medical_check(mc) for mc in medical_checks]

        # 3. Format payload
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": self.settings.system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "patient_info": anonymized_patient,
                            "medical_history": anonymized_checks,
                        },
                        indent=4,
                    ),
                },
            ],
        }

        ai_request = AiRequest(
            patient_id=patient_id,
            model_name=self.settings.model,
            model_url=self.settings.url,
            system_prompt_text=self.settings.system_prompt,
            request_payload_json=json.dumps(payload),
        )
        self.db.ai_requests.save(ai_request)

        # 5. Send to OpenAI (if API key is present)
        ai_response = None
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=payload["messages"],  # type: ignore
                    timeout=self.settings.timeout,
                )

                # Save response to DB
                ai_response = AiResponse(request_id=ai_request.id, response_json=response.model_dump_json())  # type: ignore
                self.db.ai_responses.save(ai_response)
            except Exception as e:
                # In a real app we'd log this and maybe store error status
                print(f"Error calling OpenAI: {e}")
                raise

        return ai_request, ai_response

    def _anonymize_patient(self, patient: Patient) -> dict[str, Any]:
        data_json = patient.model_dump_json(
            exclude={"first_name", "middle_name", "last_name", "address", "email", "phone"}
        )
        return json.loads(data_json)

    def _anonymize_medical_check(self, mc: MedicalCheck) -> dict[str, Any]:
        data = json.loads(mc.model_dump_json())
        # Attachments already have metadata (filename, content_type).
        # We use the stored parsed_content if available.
        for i, attachment in enumerate(mc.attachments):
            if attachment.parsed_content:
                data["attachments"][i]["content"] = attachment.parsed_content
        return data

    def _read_attachment_content(self, relative_path: str) -> str | None:
        """Reads text content of an attachment if it is a text file or PDF."""
        full_path = Path("attachments") / relative_path
        if not full_path.exists() or not full_path.is_file():
            return None

        suffix = full_path.suffix.lower()

        # Handle PDF files
        if suffix == ".pdf":
            try:
                reader = PdfReader(full_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except Exception as e:
                print(f"Error reading PDF attachment {full_path}: {e}")
                return None

        # Simple check for text files by extension
        text_extensions = {".txt", ".csv", ".json", ".xml", ".md"}
        if suffix not in text_extensions:
            return None

        try:
            # We assume UTF-8 for now.
            return full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading text attachment {full_path}: {e}")
            return None
