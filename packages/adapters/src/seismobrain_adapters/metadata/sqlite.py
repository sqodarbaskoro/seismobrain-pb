"""
File: sqlite.py
Description: SQLite MetadataStore adapter for Starter tier
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

from seismobrain_adapters.metadata.sqlalchemy_store import SqlAlchemyMetadataStore


class SqliteMetadataStore(SqlAlchemyMetadataStore):
    """Starter-tier MetadataStore backed by SQLite (SQLAlchemy)."""

    def __init__(self, db_path: Path | str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(f"sqlite+pysqlite:///{path}")
