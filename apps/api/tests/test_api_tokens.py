"""
File: test_api_tokens.py
Description: Scoped expiring revocable API tokens (T4.4)
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
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    return AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )


def test_api_token_scope_expiry_revoke(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    issued = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["read"], "ttl_seconds": 3600},
        headers=headers,
    )
    assert issued.status_code == 201
    token = issued.json()["token"]
    token_id = issued.json()["id"]
    ok = client.post(
        "/api/v1/api-tokens/authenticate",
        headers={"Authorization": f"Bearer {token}", "X-Required-Scope": "read"},
    )
    assert ok.status_code == 200
    denied = client.post(
        "/api/v1/api-tokens/authenticate",
        headers={"Authorization": f"Bearer {token}", "X-Required-Scope": "admin"},
    )
    assert denied.status_code == 403
    revoked = client.post(f"/api/v1/api-tokens/{token_id}/revoke", headers=headers)
    assert revoked.json()["revoked"] is True
    after = client.post(
        "/api/v1/api-tokens/authenticate",
        headers={"Authorization": f"Bearer {token}", "X-Required-Scope": "read"},
    )
    assert after.status_code == 403


def test_list_tokens_never_includes_the_raw_secret(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["read"], "ttl_seconds": 3600},
        headers=headers,
    )
    listed = client.get("/api/v1/api-tokens", headers=headers)
    assert listed.status_code == 200
    tokens = listed.json()["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["name"] == "ci"
    assert tokens[0]["revoked"] is False
    assert "token" not in tokens[0]
    assert "token_hash" not in tokens[0]

    # Another user's tokens never show up here.
    other = client.get("/api/v1/api-tokens", headers={"X-User-Id": "u2"})
    assert other.json()["tokens"] == []


def test_issue_rejects_unsupported_scope(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    resp = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["write"], "ttl_seconds": 3600},
        headers={"X-User-Id": "u1"},
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("ttl_seconds", [0, -1, 60 * 60 * 24 * 90 + 1])
def test_issue_rejects_out_of_bounds_ttl(container: AppContainer, ttl_seconds: int) -> None:
    client = TestClient(create_app(container))
    resp = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["read"], "ttl_seconds": ttl_seconds},
        headers={"X-User-Id": "u1"},
    )
    assert resp.status_code == 422


def test_issue_accepts_the_website_default_90_day_ttl(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    resp = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["read"], "ttl_seconds": 60 * 60 * 24 * 90},
        headers={"X-User-Id": "u1"},
    )
    assert resp.status_code == 201


def test_api_token_delete_removes_key(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    token_id = client.post(
        "/api/v1/api-tokens", json={"name": "x", "scopes": ["read"]}, headers=headers
    ).json()["id"]
    assert client.delete(f"/api/v1/api-tokens/{token_id}", headers=headers).json()["deleted"]
    assert client.get("/api/v1/api-tokens", headers=headers).json()["tokens"] == []
    assert client.delete(f"/api/v1/api-tokens/{token_id}", headers=headers).status_code == 404
