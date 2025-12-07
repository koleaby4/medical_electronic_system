from __future__ import annotations

import sqlite3

from src.data_access.base import BaseStorage
from src.models.medical_check_template import (
    MedicalCheckTemplateItem,
    MedicalCheckTemplate,
)


class MedicalCheckTemplateStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def close(self) -> None:
        return None

    def list_medical_check_names(self) -> list[MedicalCheckTemplate]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT medical_check_name_id AS template_id, medical_check_name AS template_name
                FROM medical_check_names
                ORDER BY medical_check_name COLLATE NOCASE
                """
            )
            rows = self._fetch_all_dicts(cur)
        finally:
            cur.close()

        return [
            MedicalCheckTemplate(
                template_id=r.get("template_id"),
                template_name=r.get("template_name"),
                items=[],
            )
            for r in rows
        ]

    def get_template(self, *, template_id: int) -> MedicalCheckTemplate | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT medical_check_name_id AS template_id, medical_check_name AS template_name
                FROM medical_check_names
                WHERE medical_check_name_id = ?
                """,
                [template_id],
            )
            header = self._fetch_one_dict(cur)
            if not header:
                return None

            cur.execute(
                """
                SELECT name, units, input_type, placeholder
                FROM medical_check_template_items
                WHERE medical_check_name_id = ?
                ORDER BY rowid ASC
                """,
                [template_id],
            )
            items = [
                MedicalCheckTemplateItem(
                    name=(r[0] or ""),
                    units=(r[1] or ""),
                    input_type=(r[2] or "short_text"),
                    placeholder=(r[3] or ""),
                )
                for r in cur.fetchall()
            ]
        finally:
            cur.close()

        return MedicalCheckTemplate(
            template_id=header.get("template_id"),
            template_name=header.get("template_name"),
            items=items,
        )

    def upsert(
        self,
        *,
        template_id: int | None,
        template_name: str,
        items: list[MedicalCheckTemplateItem],
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO medical_check_names (medical_check_name_id, medical_check_name)
            VALUES (?, ?) ON CONFLICT(medical_check_name_id) DO
            UPDATE SET
                medical_check_name = excluded.medical_check_name
            """,
            [template_id, template_name],
        )

        if template_id is None:
            template_id = int(cur.lastrowid)

        self.conn.execute(
            "DELETE FROM medical_check_template_items WHERE medical_check_name_id = ?",
            [template_id],
        )

        for idx, item in enumerate(items):
            name = (item.name or "").strip()
            units = (item.units or "").strip()
            input_type = (item.input_type or "number").strip()
            placeholder = (item.placeholder or "").strip()

            self.conn.execute(
                """
                INSERT INTO medical_check_template_items (medical_check_name_id, name, units, input_type, placeholder)
                VALUES (?, ?, ?, ?, ?)
                """,
                [template_id, name, units, input_type, placeholder],
            )

        self.conn.commit()
        return template_id
