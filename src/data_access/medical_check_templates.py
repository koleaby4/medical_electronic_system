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

    def list_medical_check_templates(self) -> list[MedicalCheckTemplate]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT template_id, template_name
                FROM medical_check_templates
                ORDER BY template_name COLLATE NOCASE
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
                SELECT template_id, template_name
                FROM medical_check_templates
                WHERE template_id = ?
                """,
                [template_id],
            )
            header = self._fetch_one_dict(cur)
            if not header:
                return None

            cur.execute(
                """
                SELECT name, units, input_type, placeholder, sort_order
                FROM medical_check_template_items
                WHERE template_id = ?
                ORDER BY sort_order ASC, rowid ASC
                """,
                [template_id],
            )
            items = [
                MedicalCheckTemplateItem(
                    name=(r[0] or ""),
                    units=(r[1] or ""),
                    input_type=(r[2] or "short_text"),
                    placeholder=(r[3] or ""),
                    sort_order=r[4],
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
            INSERT INTO medical_check_templates (template_id, template_name)
            VALUES (?, ?) ON CONFLICT(template_id) DO
            UPDATE SET
                template_name = excluded.template_name
            """,
            [template_id, template_name],
        )

        if template_id is None:
            template_id = int(cur.lastrowid)

        self.conn.execute(
            "DELETE FROM medical_check_template_items WHERE template_id = ?",
            [template_id],
        )

        for idx, item in enumerate(items):
            # Pull values from model and normalize like existing code
            name = (item.name or "").strip()
            units = (item.units or "").strip()
            input_type = (item.input_type or "short_text").strip()
            placeholder = (item.placeholder or "").strip()

            self.conn.execute(
                """
                INSERT INTO medical_check_template_items (template_id, name, units, input_type, placeholder, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [template_id, name, units, input_type, placeholder, idx],
            )

        self.conn.commit()
        return template_id
