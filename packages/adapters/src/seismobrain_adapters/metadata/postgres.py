"""
File: postgres.py
Description: PostgreSQL MetadataStore adapter for Team/Production tiers
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

from sqlalchemy.engine import make_url

from seismobrain_adapters.metadata.sqlalchemy_store import SqlAlchemyMetadataStore


def _normalize_postgres_url(url: str) -> str:
    """Prefer psycopg (v3) driver; testcontainers may return psycopg2-style URLs."""
    parsed = make_url(url)
    if parsed.drivername in {"postgresql", "postgresql+psycopg2"}:
        parsed = parsed.set(drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)


class PostgresMetadataStore(SqlAlchemyMetadataStore):
    """Team-tier MetadataStore backed by PostgreSQL (SQLAlchemy)."""

    def __init__(self, database_url: str) -> None:
        super().__init__(_normalize_postgres_url(database_url))
