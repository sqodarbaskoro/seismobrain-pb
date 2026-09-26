"""
File: test_auth_bearer.py
Description: Bearer JWT principal resolution and /auth/me (SPA auth path)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
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
    monkeypatch.setenv("REGISTRATION_MODE", "open")
    monkeypatch.setenv("PUBLIC_URL", "http://127.0.0.1:8080")
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
    return TestClient(create_app(container), base_url="http://testserver")


def test_auth_status_reports_empty_then_has_users(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    status = client.get("/auth/status")
    assert status.status_code == 200
    assert status.json() == {
        "has_users": False,
        "registration_mode": "open",
    }
    client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "long-enough-pass", "name": "A"},
    )
    after = client.get("/auth/status")
    assert after.json()["has_users"] is True


def test_bearer_token_resolves_me_and_admin_header_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    reg = client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "long-enough-pass", "name": "Admin"},
    )
    assert reg.status_code == 201
    assert reg.json()["status"] == "active"
    assert reg.json()["system_role"] == "system_admin"

    login = client.post(
        "/auth/token",
        json={"email": "admin@example.com", "password": "long-enough-pass"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    set_cookie = login.headers.get("set-cookie", "")
    assert "Secure" not in set_cookie

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "admin@example.com"
    assert body["system_role"] == "system_admin"
    assert body["id"]

    denied = client.get("/auth/me")
    assert denied.status_code == 401

    # Test helper headers still work without Bearer.
    helper = client.get("/auth/me", headers={"X-User-Id": body["id"], "X-System-Role": "user"})
    assert helper.status_code == 200
    assert helper.json()["system_role"] == "user"


def test_first_admin_bootstrap_second_user_follows_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("REGISTRATION_MODE", "approval")
    monkeypatch.setenv("PUBLIC_URL", "http://127.0.0.1:8080")
    settings = Settings()  # type: ignore[call-arg]
    client = TestClient(
        create_app(
            AppContainer(
                settings=settings,
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
    first = client.post(
        "/auth/register",
        json={"email": "first@example.com", "password": "long-enough-pass", "name": "First"},
    )
    assert first.status_code == 201
    assert first.json()["status"] == "active"
    assert first.json()["system_role"] == "system_admin"

    second = client.post(
        "/auth/register",
        json={"email": "second@example.com", "password": "long-enough-pass", "name": "Second"},
    )
    assert second.status_code == 201
    assert second.json()["status"] == "pending"
    assert second.json()["system_role"] == "user"
