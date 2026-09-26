"""
File: test_openapi_production.py
Description: Interactive docs disabled in production; OpenAPI admin-only (SEC-11)
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


def _client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, environment: str
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("ENVIRONMENT", environment)
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
    )
    return TestClient(create_app(container))


def test_production_disables_docs_and_restricts_openapi(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch, environment="production")
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 403
    ok = client.get("/openapi.json", headers={"X-System-Role": "system_admin"})
    assert ok.status_code == 200
    assert "openapi" in ok.json()


def test_non_production_keeps_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch, environment="development")
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
