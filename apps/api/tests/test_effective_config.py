"""
File: test_effective_config.py
Description: Effective configuration view with sources and hash, admin-only (T4.21)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
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


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("AIR_GAPPED", "false")
    return TestClient(
        create_app(
            AppContainer(
                settings=Settings(),  # type: ignore[call-arg]
                metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
                job_queue=InProcessJobQueue(tmp_path / "jobs"),
                object_store=FilesystemObjectStore(tmp_path / "objects"),
                event_log=InMemoryEventLog(),
                rate_limiter=InMemoryRateLimiter(),
                authorization_guard=DenyAllAuthorizationGuard(),
                user_store=InMemoryUserStore(),
            )
        )
    )


def test_effective_config_shows_sources_and_hash(client: TestClient) -> None:
    response = client.get(
        "/api/v1/admin/effective-config",
        headers={"X-System-Role": "system_admin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "config_hash" in body and len(body["config_hash"]) == 64
    assert body["config"]["sb_tier"]["value"] == "starter"
    assert body["config"]["sb_tier"]["source"] == "env:SB_TIER"
    assert body["config"]["air_gapped"]["source"] == "env:AIR_GAPPED"


def test_effective_config_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/admin/effective-config")
    assert response.status_code == 401


def test_effective_config_rejects_non_admin(client: TestClient) -> None:
    response = client.get(
        "/api/v1/admin/effective-config",
        headers={"X-User-Id": "u1", "X-System-Role": "user"},
    )
    assert response.status_code == 403
