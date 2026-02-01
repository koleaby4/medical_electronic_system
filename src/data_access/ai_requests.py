import sqlite3

from src.data_access.base import BaseStorage
from src.models.ai_request import AiRequest


class AiRequestsStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def save(self, request: AiRequest) -> AiRequest:
        cur = self.conn.execute(
            """
            INSERT INTO ai_requests (
                patient_id, model_name, model_url, system_prompt_text, request_payload_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                request.patient_id,
                request.model_name,
                request.model_url,
                request.system_prompt_text,
                request.request_payload_json,
            ],
        )

        if request.id is None:
            request.id = int(cur.lastrowid)

        # Reload to get created_at if needed, but for now we just return the object
        self.conn.commit()
        return request

    def get_by_patient(self, patient_id: int) -> list[AiRequest]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, patient_id, model_name, model_url, system_prompt_text, request_payload_json, created_at
                FROM ai_requests
                WHERE patient_id = ?
                ORDER BY created_at DESC
                """,
                [patient_id],
            )
            return [AiRequest(**r) for r in self._fetch_all_dicts(cur)]
        finally:
            cur.close()
