"""
File: test_admin_users.py
Description: Admin user approve/disable/roles/session revoke (FR-ADM-01)
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


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("REGISTRATION_MODE", "approval")
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
    return TestClient(create_app(container), base_url="https://testserver")


def test_approve_disable_role_and_session_revoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    bootstrap = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "long-enough-pass",
            "name": "Admin",
        },
    )
    assert bootstrap.status_code == 201
    assert bootstrap.json()["system_role"] == "system_admin"

    created = client.post(
        "/auth/register",
        json={"email": "p@example.com", "password": "long-enough-pass", "name": "P"},
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    assert created.json()["status"] == "pending"
    admin = {"X-System-Role": "system_admin"}
    assert (
        client.post(f"/admin/users/{user_id}/approve", headers=admin).status_code == 200
    )
    role = client.post(
        f"/admin/users/{user_id}/role",
        headers=admin,
        json={"system_role": "user"},
    )
    assert role.status_code == 200
    assert role.json()["system_role"] == "user"
    login = client.post(
        "/auth/token",
        json={"email": "p@example.com", "password": "long-enough-pass"},
    )
    assert login.status_code == 200
    revoked = client.post(
        f"/admin/users/{user_id}/sessions/revoke", headers=admin
    )
    assert revoked.status_code == 200
    disabled = client.post(f"/admin/users/{user_id}/disable", headers=admin)
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
    blocked = client.post(
        "/auth/token",
        json={"email": "p@example.com", "password": "long-enough-pass"},
    )
    assert blocked.status_code == 403
