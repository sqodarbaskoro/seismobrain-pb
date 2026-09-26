"""
File: test_app_skeleton.py
Description: FastAPI app skeleton DI wiring and health route stub tests
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
from seismobrain_api.app import AppContainer, create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def container(tmp_path: Path, settings: Settings) -> AppContainer:
    return AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )


def test_create_app_wires_ports_and_config(container: AppContainer) -> None:
    app = create_app(container)
    deps: AppContainer = app.state.container
    assert deps is container
    assert deps.settings is container.settings
    assert deps.metadata_store is container.metadata_store
    assert deps.job_queue is container.job_queue
    assert deps.object_store is container.object_store
    assert deps.event_log is container.event_log
    assert deps.rate_limiter is container.rate_limiter
    assert deps.authorization_guard is container.authorization_guard


def test_health_stub_and_metrics_registered(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "sb_chunk_overflow_total" in metrics.text


def test_routers_registered(container: AppContainer) -> None:
    app = create_app(container)
    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/metrics" in paths
