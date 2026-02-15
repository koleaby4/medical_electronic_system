import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.models.ai_request import AiRequest
from src.models.ai_response import AiResponse
from src.services.ai_service import AiService


class MockAiService(AiService):
    def __init__(self, db, settings):
        super().__init__(db, settings)
        self.mock_mode = os.getenv("AI_MOCK_MODE", "live")
        self.fixtures_dir = Path(os.getenv("AI_FIXTURES_DIR", "tests/fixtures/ai_responses"))

    async def prepare_and_send_request(self, patient_id: int) -> tuple[AiRequest, AiResponse | None]:
        if self.mock_mode == "live":
            return await super().prepare_and_send_request(patient_id)

        # 1. Collect data (same as super)
        patient = self.db.patients.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        medical_checks = self.db.medical_checks.get_medical_checks(patient_id)
        anonymized_patient = self._anonymize_patient(patient)
        anonymized_checks = [self._anonymize_medical_check(mc) for mc in medical_checks]

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
                        indent=2,
                    ),
                },
            ],
        }

        cache_key = self._generate_cache_key(payload)
        cache_file = self.fixtures_dir / f"{cache_key}.json"

        if self.mock_mode == "playback":
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)

                ai_request = AiRequest(
                    patient_id=patient_id,
                    model_name=self.settings.model,
                    model_url=self.settings.url,
                    system_prompt_text=self.settings.system_prompt,
                    request_payload_json=json.dumps(payload),
                )
                self.db.ai_requests.save(ai_request)

                ai_response = AiResponse(request_id=ai_request.id, response_json=json.dumps(cached_data))  # type: ignore
                self.db.ai_responses.save(ai_response)
                return ai_request, ai_response
            else:
                # If no fixture found, return a dummy response instead of failing
                # This makes tests more robust if they don't strictly depend on AI content
                dummy_content = {
                    "Overview": {
                        "text": "Dummy AI overview for testing.",
                        "html": "<p>Dummy AI overview for testing.</p>",
                    },
                    "Charts": [],
                }
                ai_request = AiRequest(
                    patient_id=patient_id,
                    model_name=self.settings.model,
                    model_url=self.settings.url,
                    system_prompt_text=self.settings.system_prompt,
                    request_payload_json=json.dumps(payload),
                )
                self.db.ai_requests.save(ai_request)
                ai_response = AiResponse(
                    request_id=ai_request.id,  # type: ignore
                    response_json=json.dumps({"choices": [{"message": {"content": json.dumps(dummy_content)}}]}),
                )
                self.db.ai_responses.save(ai_response)
                return ai_request, ai_response

        # Record mode
        ai_request_rec, ai_response_rec = await super().prepare_and_send_request(patient_id)

        if ai_response_rec:
            self.fixtures_dir.mkdir(parents=True, exist_ok=True)
            # OpenAI response is in ai_response.response_json
            resp_data = json.loads(ai_response_rec.response_json)
            with open(cache_file, "w") as f:
                json.dump(resp_data, f, indent=2)

        return ai_request_rec, ai_response_rec

    def _generate_cache_key(self, payload: dict[str, Any]) -> str:
        key_data = {
            "model": payload.get("model"),
            "messages": payload.get("messages"),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()
