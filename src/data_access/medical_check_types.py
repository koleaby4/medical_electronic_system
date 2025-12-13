from __future__ import annotations

import sqlite3

from src.data_access.base import BaseStorage
from src.models.medical_check_type import (
    MedicalCheckType,
    MedicalCheckTypeItem,
)


class MedicalCheckTypesStorage(BaseStorage):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    def list_medical_check_types(self) -> list[MedicalCheckType]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT type_id,
                       name
                FROM medical_check_types
                ORDER BY name COLLATE NOCASE
                """
            )
            rows = self._fetch_all_dicts(cur)
        finally:
            cur.close()

        return [
            MedicalCheckType(
                type_id=r.get("type_id"),
                name=r.get("name"),
                items=[],
            )
            for r in rows
        ]

    def get_check_type(self, *, type_id: int) -> MedicalCheckType | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT type_id,
                       name
                FROM medical_check_types
                WHERE type_id = ?
                """,
                [type_id],
            )
            header = self._fetch_one_dict(cur)
            if not header:
                return None

            cur.execute(
                """
                SELECT name, units, input_type, placeholder
                FROM medical_check_type_items
                WHERE type_id = ?
                ORDER BY rowid ASC
                """,
                [type_id],
            )
            items = [
                MedicalCheckTypeItem(
                    name=(r[0] or ""),
                    units=(r[1] or ""),
                    input_type=(r[2] or "short_text"),
                    placeholder=(r[3] or ""),
                )
                for r in cur.fetchall()
            ]
        finally:
            cur.close()

        return MedicalCheckType(
            type_id=header.get("type_id"),
            name=header.get("name"),
            items=items,
        )

    def upsert(
        self,
        *,
        template_id: int | None,
        check_name: str,
        items: list[MedicalCheckTypeItem],
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO medical_check_types (type_id, name)
            VALUES (?, ?) ON CONFLICT(type_id) DO
            UPDATE SET
                name = excluded.name
            """,
            [template_id, check_name],
        )

        if template_id is None:
            template_id = int(cur.lastrowid)

        self.conn.execute(
            "DELETE FROM medical_check_type_items WHERE type_id = ?",
            [template_id],
        )

        for idx, item in enumerate(items):
            name = (item.name or "").strip()
            units = (item.units or "").strip()
            input_type = (item.input_type or "number").strip()
            placeholder = (item.placeholder or "").strip()

            self.conn.execute(
                """
                INSERT INTO medical_check_type_items (type_id, name, units, input_type, placeholder)
                VALUES (?, ?, ?, ?, ?)
                """,
                [template_id, name, units, input_type, placeholder],
            )

        self.conn.commit()
        return template_id

    def delete(self, *, type_id: int) -> None:
        self.conn.execute("DELETE FROM medical_check_types WHERE type_id = ?", [type_id])
        self.conn.commit()
