"""
File: test_auth_registration.py
Description: Email/password registration modes and pending-user token block (FR-AUTH-01)
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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str,
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("REGISTRATION_MODE", mode)
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


def test_approval_mode_creates_pending_user_without_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch, mode="approval")
    # First registrant bootstraps as system_admin; seed that user first.
    bootstrap = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "long-enough-pass",
            "name": "Admin",
        },
    )
    assert bootstrap.status_code == 201
    assert bootstrap.json()["status"] == "active"
    assert bootstrap.json()["system_role"] == "system_admin"

    response = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "long-enough-pass", "name": "A"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert "access_token" not in body
    login = client.post(
        "/auth/token",
        json={"email": "a@example.com", "password": "long-enough-pass"},
    )
    assert login.status_code == 403
    assert login.json()["detail"] == "pending approval"


def test_closed_mode_rejects_registration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch, mode="closed")
    response = client.post(
        "/auth/register",
        json={"email": "b@example.com", "password": "long-enough-pass", "name": "B"},
    )
    assert response.status_code == 403


def test_open_mode_active_user_can_obtain_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch, mode="open")
    response = client.post(
        "/auth/register",
        json={"email": "c@example.com", "password": "long-enough-pass", "name": "C"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "active"
    login = client.post(
        "/auth/token",
        json={"email": "c@example.com", "password": "long-enough-pass"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]
