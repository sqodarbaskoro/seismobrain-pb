"""
File: inline.py
Description: SQLite inline EvidenceSnapshotStore for Starter tier
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

import hashlib
import sqlite3
from pathlib import Path


class InlineEvidenceSnapshotStore:
    """Starter EvidenceSnapshotStore with inline SQLite blobs."""

    def __init__(self, db_path: Path | str) -> None:
        if str(db_path) == ":memory:":
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_snapshots (
                    uri TEXT PRIMARY KEY,
                    text TEXT NOT NULL
                )
                """
            )
            self._conn.commit()
            return
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_snapshots (
                uri TEXT PRIMARY KEY,
                text TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def put(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = f"inline:{digest}"
        self._conn.execute(
            """
            INSERT INTO evidence_snapshots(uri, text) VALUES (?, ?)
            ON CONFLICT(uri) DO NOTHING
            """,
            (uri, text),
        )
        self._conn.commit()
        return uri

    def get(self, uri: str) -> str:
        row = self._conn.execute(
            "SELECT text FROM evidence_snapshots WHERE uri=?", (uri,)
        ).fetchone()
        if row is None:
            raise KeyError(uri)
        return str(row[0])
