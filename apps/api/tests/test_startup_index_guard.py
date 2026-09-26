"""
File: test_startup_index_guard.py
Description: FR-IDX-06 — startup refuses model/dimension/Qdrant version mismatch
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

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.startup_index_guard import (
    ActiveIndexInfo,
    ConfiguredIndexInfo,
    StartupIndexError,
    assert_startup_index_compatible,
)


def test_compatible_index_passes() -> None:
    assert_startup_index_compatible(
        configured=ConfiguredIndexInfo(embedding_model="cpu-hash", embedding_dimension=32),
        active=ActiveIndexInfo(
            embedding_model="cpu-hash",
            embedding_dimension=32,
            qdrant_version="1.19.1",
        ),
    )


def test_model_mismatch_refused() -> None:
    with pytest.raises(StartupIndexError, match="embedding model mismatch"):
        assert_startup_index_compatible(
            configured=ConfiguredIndexInfo(
                embedding_model="cpu-hash", embedding_dimension=32
            ),
            active=ActiveIndexInfo(
                embedding_model="other-model",
                embedding_dimension=32,
                qdrant_version="1.19.1",
            ),
        )


def test_dimension_mismatch_refused() -> None:
    with pytest.raises(StartupIndexError, match="embedding dimension mismatch"):
        assert_startup_index_compatible(
            configured=ConfiguredIndexInfo(
                embedding_model="cpu-hash", embedding_dimension=32
            ),
            active=ActiveIndexInfo(
                embedding_model="cpu-hash",
                embedding_dimension=768,
                qdrant_version="1.19.1",
            ),
        )


def test_old_qdrant_version_refused() -> None:
    with pytest.raises(StartupIndexError, match="older than minimum"):
        assert_startup_index_compatible(
            configured=ConfiguredIndexInfo(
                embedding_model="cpu-hash", embedding_dimension=32
            ),
            active=ActiveIndexInfo(
                embedding_model="cpu-hash",
                embedding_dimension=32,
                qdrant_version="1.18.9",
            ),
        )


def _container(tmp_path: Path, settings: Settings) -> AppContainer:
    return AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        configured_index=ConfiguredIndexInfo(
            embedding_model="cpu-hash", embedding_dimension=32
        ),
        active_index=ActiveIndexInfo(
            embedding_model="cpu-hash",
            embedding_dimension=64,
            qdrant_version="1.19.1",
        ),
    )


def test_create_app_refuses_incompatible_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    settings = Settings()  # type: ignore[call-arg]
    with pytest.raises(StartupIndexError, match="embedding dimension mismatch"):
        create_app(_container(tmp_path, settings))


def test_create_app_serves_when_index_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    settings = Settings()  # type: ignore[call-arg]
    container = AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        configured_index=ConfiguredIndexInfo(
            embedding_model="cpu-hash", embedding_dimension=32
        ),
        active_index=ActiveIndexInfo(
            embedding_model="cpu-hash",
            embedding_dimension=32,
            qdrant_version="1.19.1",
        ),
    )
    client = TestClient(create_app(container))
    assert client.get("/health").status_code == 200
