from __future__ import annotations

from typing import Any
import sqlite3


class BaseStorage:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _fetch_all_dicts(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
        cols: list[str] = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    @staticmethod
    def _fetch_one_dict(cur: sqlite3.Cursor) -> dict[str, Any] | None:
        desc = cur.description
        if not desc:
            return None
        cols: list[str] = [d[0] for d in desc]
        if row := cur.fetchone():
            return dict(zip(cols, row))

        return None
