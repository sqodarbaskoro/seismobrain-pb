"""
File: postgres.py
Description: PostgreSQL SparseTermRegistry with in-process LRU for Team tier
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

import threading
from collections import OrderedDict

from sqlalchemy import Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class SparseTermRow(Base):
    __tablename__ = "sparse_term_registry"
    __table_args__ = (
        UniqueConstraint("encoder_version", "arm", "idx", name="uq_sparse_idx"),
    )

    encoder_version: Mapped[str] = mapped_column(String(64), primary_key=True)
    arm: Mapped[str] = mapped_column(String(64), primary_key=True)
    token: Mapped[str] = mapped_column(String(512), primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)


def _normalize_postgres_url(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername in {"postgresql", "postgresql+psycopg2"}:
        parsed = parsed.set(drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)


class PostgresSparseTermRegistry:
    """Team SparseTermRegistry: PostgreSQL authority + in-process LRU cache."""

    def __init__(self, database_url: str, *, lru_capacity: int = 10_000) -> None:
        if lru_capacity < 1:
            raise ValueError("lru_capacity must be >= 1")
        self._engine = create_engine(_normalize_postgres_url(database_url), future=True)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(
            self._engine, expire_on_commit=False, class_=Session
        )
        self._lock = threading.Lock()
        self._lru: OrderedDict[tuple[str, str, str], int] = OrderedDict()
        self._lru_capacity = lru_capacity

    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int:
        key = (encoder_version, arm, token)
        with self._lock:
            if key in self._lru:
                self._lru.move_to_end(key)
                return self._lru[key]
        with self._session_factory() as session:
            existing = session.get(SparseTermRow, key)
            if existing is not None:
                self._cache_put(key, existing.idx)
                return existing.idx
            max_idx = session.scalar(
                select(SparseTermRow.idx)
                .where(
                    SparseTermRow.encoder_version == encoder_version,
                    SparseTermRow.arm == arm,
                )
                .order_by(SparseTermRow.idx.desc())
                .limit(1)
            )
            idx = 0 if max_idx is None else int(max_idx) + 1
            session.add(
                SparseTermRow(
                    encoder_version=encoder_version,
                    arm=arm,
                    token=token,
                    idx=idx,
                )
            )
            session.commit()
            self._cache_put(key, idx)
            return idx

    def _cache_put(self, key: tuple[str, str, str], idx: int) -> None:
        with self._lock:
            self._lru[key] = idx
            self._lru.move_to_end(key)
            while len(self._lru) > self._lru_capacity:
                self._lru.popitem(last=False)

    def close(self) -> None:
        self._engine.dispose()
