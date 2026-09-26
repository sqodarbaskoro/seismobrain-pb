"""
File: sqlite.py
Description: SQLite SparseTermRegistry for Starter tier
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
import threading
from pathlib import Path


class SqliteSparseTermRegistry:
    """Starter SparseTermRegistry backed by SQLite with unique token/index constraints."""

    def __init__(self, db_path: Path | str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sparse_term_registry (
                encoder_version TEXT NOT NULL,
                arm TEXT NOT NULL,
                token TEXT NOT NULL,
                idx INTEGER NOT NULL,
                PRIMARY KEY (encoder_version, arm, token),
                UNIQUE (encoder_version, arm, idx)
            )
            """
        )
        self._conn.commit()

    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT idx FROM sparse_term_registry
                WHERE encoder_version=? AND arm=? AND token=?
                """,
                (encoder_version, arm, token),
            ).fetchone()
            if row is not None:
                return int(row[0])
            next_row = self._conn.execute(
                """
                SELECT COALESCE(MAX(idx), -1) + 1 FROM sparse_term_registry
                WHERE encoder_version=? AND arm=?
                """,
                (encoder_version, arm),
            ).fetchone()
            idx = int(next_row[0])
            self._conn.execute(
                """
                INSERT INTO sparse_term_registry(encoder_version, arm, token, idx)
                VALUES (?, ?, ?, ?)
                """,
                (encoder_version, arm, token, idx),
            )
            self._conn.commit()
            return idx

    def close(self) -> None:
        self._conn.close()
