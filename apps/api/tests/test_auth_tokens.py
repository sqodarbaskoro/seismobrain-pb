"""
File: test_auth_tokens.py
Description: Access token + rotating refresh cookie tests (FR-AUTH-02, SEC-04)
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
from seismobrain_api.auth.tokens import (
    REFRESH_COOKIE_NAME,
    access_token_ttl_seconds,
)
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings

_CSRF_HEADER = "X-CSRF-Token"


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("REGISTRATION_MODE", "open")
    monkeypatch.setenv("PUBLIC_URL", "https://testserver")
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


def _register_and_login(client: TestClient) -> tuple[str, str, str]:
    client.post(
        "/auth/register",
        json={"email": "t@example.com", "password": "long-enough-pass", "name": "T"},
    )
    login = client.post(
        "/auth/token",
        json={"email": "t@example.com", "password": "long-enough-pass"},
    )
    assert login.status_code == 200
    body = login.json()
    access = body["access_token"]
    csrf = body["csrf_token"]
    assert REFRESH_COOKIE_NAME in login.cookies
    set_cookie = login.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=strict" in set_cookie or "SameSite=Strict" in set_cookie
    assert "Path=/auth" in set_cookie
    return access, csrf, login.cookies[REFRESH_COOKIE_NAME]


def test_login_issues_short_access_and_refresh_cookie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    access, csrf, refresh = _register_and_login(client)
    assert access
    assert csrf
    assert refresh
    remaining = access_token_ttl_seconds(access, "a" * 64)
    assert 0 < remaining <= 15 * 60


def test_refresh_rotates_and_requires_csrf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    _, csrf, _ = _register_and_login(client)
    missing = client.post("/auth/refresh")
    assert missing.status_code == 403
    ok = client.post("/auth/refresh", headers={_CSRF_HEADER: csrf})
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    assert ok.json()["csrf_token"]
    assert REFRESH_COOKIE_NAME in ok.cookies


def test_refresh_reuse_revokes_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    _, csrf, old_refresh = _register_and_login(client)
    first = client.post("/auth/refresh", headers={_CSRF_HEADER: csrf})
    assert first.status_code == 200
    new_csrf = first.json()["csrf_token"]
    second = client.post("/auth/refresh", headers={_CSRF_HEADER: new_csrf})
    assert second.status_code == 200
    reuse_client = TestClient(
        client.app, base_url="https://testserver", cookies={REFRESH_COOKIE_NAME: old_refresh}
    )
    reuse = reuse_client.post(
        "/auth/refresh",
        headers={_CSRF_HEADER: second.json()["csrf_token"]},
    )
    assert reuse.status_code == 401
    # Current rotated cookie must also be dead after family revoke.
    after = client.post(
        "/auth/refresh",
        headers={_CSRF_HEADER: second.json()["csrf_token"]},
    )
    assert after.status_code == 401
