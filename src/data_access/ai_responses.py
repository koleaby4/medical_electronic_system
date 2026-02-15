import sqlite3

from src.data_access.base import BaseStorage
from src.models.ai_response import AiResponse


class AiResponsesStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def save(self, response: AiResponse) -> AiResponse:
        cur = self.conn.execute(
            """
            INSERT INTO ai_responses (
                request_id, response_json
            )
            VALUES (?, ?)
            """,
            [
                response.request_id,
                response.response_json,
            ],
        )

        if response.id is None and cur.lastrowid is not None:
            response.id = int(cur.lastrowid)

        self.conn.commit()
        return response

    def get_by_request(self, request_id: int) -> list[AiResponse]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, request_id, response_json, created_at
                FROM ai_responses
                WHERE request_id = ?
                ORDER BY created_at DESC
                """,
                [request_id],
            )
            return [AiResponse(**r) for r in self._fetch_all_dicts(cur)]
        finally:
            cur.close()
