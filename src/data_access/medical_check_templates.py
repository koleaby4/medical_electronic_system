from __future__ import annotations

import sqlite3

from src.data_access.base import BaseStorage
from src.models.medical_check_template import (
    MedicalCheckTemplate,
    MedicalCheckTemplateItem,
)


class MedicalCheckTemplatesStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def list_medical_check_templates(self) -> list[MedicalCheckTemplate]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    t.template_id                         AS template_id,
                    t.name                            AS type_name,
                    t.is_active                       AS is_active,
                    i.name                            AS item_name,
                    i.units                           AS item_units,
                    i.input_type                      AS item_input_type,
                    i.placeholder                     AS item_placeholder
                FROM medical_check_templates t
                LEFT JOIN medical_check_template_items i ON i.template_id = t.template_id
                ORDER BY t.name COLLATE NOCASE ASC, t.template_id ASC, i.rowid ASC
                """
            )

            check_templates_by_id: dict[int, MedicalCheckTemplate] = {}

            for (
                template_id,
                type_name,
                is_active,
                item_name,
                item_units,
                item_input_type,
                item_placeholder,
            ) in cur.fetchall():
                tid = int(template_id)
                if tid not in check_templates_by_id:
                    check_templates_by_id[tid] = MedicalCheckTemplate(
                        template_id=tid,
                        name=type_name,
                        is_active=bool(is_active),
                        items=[],
                    )

                # When there is no item (LEFT JOIN miss), item_name will be None
                if item_name:
                    check_templates_by_id[tid].items.append(
                        MedicalCheckTemplateItem(
                            name=(item_name or ""),
                            units=(item_units or ""),
                            input_type=(item_input_type or "number"),
                            placeholder=(item_placeholder or ""),
                        )
                    )
        finally:
            cur.close()

        return list(check_templates_by_id.values())

    def get_template(self, *, template_id: int) -> MedicalCheckTemplate | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT template_id,
                       name,
                       is_active
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
                SELECT name, units, input_type, placeholder
                FROM medical_check_template_items
                WHERE template_id = ?
                ORDER BY rowid ASC
                """,
                [template_id],
            )
            items = [
                MedicalCheckTemplateItem(
                    name=(r[0] or ""),
                    units=(r[1] or ""),
                    input_type=(r[2] or "number"),
                    placeholder=(r[3] or ""),
                )
                for r in cur.fetchall()
            ]
        finally:
            cur.close()

        return MedicalCheckTemplate(
            template_id=header.get("template_id"),
            name=header.get("name"),
            is_active=bool(header.get("is_active")),
            items=items,
        )

    def upsert(
        self,
        *,
        template_id: int | None,
        check_name: str,
        items: list[MedicalCheckTemplateItem],
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO medical_check_templates (template_id, name)
            VALUES (?, ?) ON CONFLICT(template_id) DO
            UPDATE SET
                name = excluded.name
            """,
            [template_id, check_name],
        )

        if template_id is None:
            template_id = int(cur.lastrowid)

        self.conn.execute(
            "DELETE FROM medical_check_template_items WHERE template_id = ?",
            [template_id],
        )

        for idx, item in enumerate(items):
            name = (item.name or "").strip()
            units = (item.units or "").strip()
            input_type = (item.input_type or "number").strip()
            placeholder = (item.placeholder or "").strip()

            self.conn.execute(
                """
                INSERT INTO medical_check_template_items (template_id, name, units, input_type, placeholder)
                VALUES (?, ?, ?, ?, ?)
                """,
                [template_id, name, units, input_type, placeholder],
            )

        self.conn.commit()
        return template_id

    def set_active_status(self, *, template_id: int, is_active: bool) -> None:
        self.conn.execute(
            "UPDATE medical_check_templates SET is_active = ? WHERE template_id = ?",
            [1 if is_active else 0, template_id],
        )
        self.conn.commit()

    def delete(self, *, template_id: int) -> None:
        self.conn.execute("DELETE FROM medical_check_templates WHERE template_id = ?", [template_id])
        self.conn.commit()
