"""
File: sqlite.py
Description: SQLite EmbeddingCache adapter for Starter tier (vectors inline)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


class SqliteEmbeddingCache:
    """Starter EmbeddingCache storing float vectors inline in SQLite."""

    def __init__(self, db_path: Path | str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                text_hash TEXT NOT NULL,
                model_id TEXT NOT NULL,
                model_revision TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                last_used_at REAL NOT NULL,
                PRIMARY KEY (text_hash, model_id, model_revision)
            )
            """
        )
        self._conn.commit()

    def get(
        self, text_hash: str, model_id: str, model_revision: str
    ) -> list[float] | None:
        row = self._conn.execute(
            """
            SELECT vector_json FROM embedding_cache
            WHERE text_hash=? AND model_id=? AND model_revision=?
            """,
            (text_hash, model_id, model_revision),
        ).fetchone()
        if row is None:
            return None
        self._conn.execute(
            """
            UPDATE embedding_cache SET last_used_at=?
            WHERE text_hash=? AND model_id=? AND model_revision=?
            """,
            (time.time(), text_hash, model_id, model_revision),
        )
        self._conn.commit()
        data = json.loads(row[0])
        return [float(x) for x in data]

    def put(
        self,
        text_hash: str,
        model_id: str,
        model_revision: str,
        *,
        vector: list[float],
    ) -> None:
        payload = json.dumps(vector)
        self._conn.execute(
            """
            INSERT INTO embedding_cache(
                text_hash, model_id, model_revision, vector_json, size_bytes, last_used_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(text_hash, model_id, model_revision) DO UPDATE SET
                vector_json=excluded.vector_json,
                size_bytes=excluded.size_bytes,
                last_used_at=excluded.last_used_at
            """,
            (text_hash, model_id, model_revision, payload, len(payload), time.time()),
        )
        self._conn.commit()

    def size_bytes(self) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) FROM embedding_cache"
        ).fetchone()
        return int(row[0])
