import json
from typing import Any

from openai import AsyncOpenAI

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
        return json.loads(mc.model_dump_json())
