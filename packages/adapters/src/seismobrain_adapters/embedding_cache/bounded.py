"""
File: bounded.py
Description: Bounded object-store EmbeddingCache for Team/Production (no PG vector blobs)
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

import sqlite3
import time
from pathlib import Path

import numpy as np

from seismobrain_core.ports import ObjectStore


def _to_f16_bytes(vector: list[float]) -> bytes:
    return np.asarray(vector, dtype=np.float16).tobytes()


def _from_f16_bytes(data: bytes) -> list[float]:
    return [float(x) for x in np.frombuffer(data, dtype=np.float16)]


class BoundedObjectEmbeddingCache:
    """Team EmbeddingCache: keys/locations in SQLite meta; vectors in ObjectStore; LRU size cap."""

    def __init__(
        self,
        *,
        object_store: ObjectStore,
        meta_db_path: Path | str,
        max_bytes: int,
    ) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be >= 1")
        self._store = object_store
        self._max_bytes = max_bytes
        path = Path(meta_db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                text_hash TEXT NOT NULL,
                model_id TEXT NOT NULL,
                model_revision TEXT NOT NULL,
                location TEXT NOT NULL,
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
            SELECT location FROM embedding_cache
            WHERE text_hash=? AND model_id=? AND model_revision=?
            """,
            (text_hash, model_id, model_revision),
        ).fetchone()
        if row is None:
            return None
        location = str(row[0])
        try:
            data = self._store.get(location)
        except KeyError:
            return None
        self._conn.execute(
            """
            UPDATE embedding_cache SET last_used_at=?
            WHERE text_hash=? AND model_id=? AND model_revision=?
            """,
            (time.time(), text_hash, model_id, model_revision),
        )
        self._conn.commit()
        return _from_f16_bytes(data)

    def put(
        self,
        text_hash: str,
        model_id: str,
        model_revision: str,
        *,
        vector: list[float],
    ) -> None:
        payload = _to_f16_bytes(vector)
        location = f"embed/{text_hash}/{model_id}/{model_revision}"
        self._store.put(location, payload)
        self._conn.execute(
            """
            INSERT INTO embedding_cache(
                text_hash, model_id, model_revision, location, size_bytes, last_used_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(text_hash, model_id, model_revision) DO UPDATE SET
                location=excluded.location,
                size_bytes=excluded.size_bytes,
                last_used_at=excluded.last_used_at
            """,
            (
                text_hash,
                model_id,
                model_revision,
                location,
                len(payload),
                time.time(),
            ),
        )
        self._conn.commit()
        self._evict_to_cap()

    def size_bytes(self) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) FROM embedding_cache"
        ).fetchone()
        return int(row[0])

    def _evict_to_cap(self) -> None:
        while self.size_bytes() > self._max_bytes:
            row = self._conn.execute(
                """
                SELECT text_hash, model_id, model_revision, location
                FROM embedding_cache
                ORDER BY last_used_at ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return
            text_hash, model_id, model_revision, location = row
            self._store.delete(str(location))
            self._conn.execute(
                """
                DELETE FROM embedding_cache
                WHERE text_hash=? AND model_id=? AND model_revision=?
                """,
                (text_hash, model_id, model_revision),
            )
            self._conn.commit()
