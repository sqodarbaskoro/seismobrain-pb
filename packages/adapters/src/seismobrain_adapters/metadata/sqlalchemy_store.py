"""
File: sqlalchemy_store.py
Description: Shared SQLAlchemy MetadataStore implementation for SQLite and PostgreSQL
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

import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from seismobrain_adapters.metadata.models import Base, TenantRow
from seismobrain_core.ports import Tenant


class SqlAlchemyMetadataStore:
    """MetadataStore backed by SQLAlchemy (shared by Starter SQLite and Team PostgreSQL)."""

    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(
            self._engine, expire_on_commit=False, class_=Session
        )

    def reset_schema(self) -> None:
        """Drop and recreate tables (test helper)."""
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)

    def create_tenant(self, name: str) -> Tenant:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("tenant name must not be blank")
        tenant = Tenant(id=str(uuid.uuid4()), name=cleaned)
        with self._session_factory() as session:
            session.add(TenantRow(id=tenant.id, name=tenant.name, settings="{}"))
            session.commit()
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        with self._session_factory() as session:
            row = session.get(TenantRow, tenant_id)
            if row is None:
                return None
            return Tenant(id=row.id, name=row.name)

    def list_tenants(self) -> list[Tenant]:
        with self._session_factory() as session:
            rows = session.scalars(select(TenantRow).order_by(TenantRow.name)).all()
            return [Tenant(id=row.id, name=row.name) for row in rows]

    def count_tenants(self) -> int:
        with self._session_factory() as session:
            return len(session.scalars(select(TenantRow.id)).all())
