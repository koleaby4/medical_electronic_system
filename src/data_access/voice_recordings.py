import sqlite3

from src.data_access.base import BaseStorage
from src.models.medical_check import VoiceRecording


class VoiceRecordingsStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def insert_recording(self, *, check_id: int, file_path: str) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO voice_recordings (check_id, file_path)
            VALUES (?, ?)
            """,
            [check_id, file_path],
        )
        return int(cur.lastrowid) if cur.lastrowid else 0

    def get_recordings_by_check_id(self, check_id: int) -> list[VoiceRecording]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT voice_recording_id, check_id, file_path, full_text, summary
                FROM voice_recordings
                WHERE check_id = ?
                """,
                [check_id],
            )
            raw_rows = self._fetch_all_dicts(cur)
            return [VoiceRecording(**row) for row in raw_rows]
        finally:
            cur.close()

    def update_transcription(self, *, voice_recording_id: int, full_text: str, summary: str | None = None) -> None:
        self.conn.execute(
            """
            UPDATE voice_recordings
            SET full_text = ?, summary = ?
            WHERE voice_recording_id = ?
            """,
            [full_text, summary, voice_recording_id],
        )
        self.conn.commit()
