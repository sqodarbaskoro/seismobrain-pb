"""
File: test_rate_limits.py
Description: Auth, chat, and upload rate limit tests (SEC-10)
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
    monkeypatch.setenv("REGISTRATION_MODE", "open")
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MIN", "3")
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MIN", "2")
    monkeypatch.setenv("UPLOAD_RATE_LIMIT_PER_HOUR", "2")
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


def test_auth_rate_limit_per_ip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(tmp_path, monkeypatch)
    for _ in range(3):
        resp = client.post(
            "/auth/token",
            json={"email": "nobody@example.com", "password": "long-enough-pass"},
        )
        assert resp.status_code in {401, 429}
    limited = client.post(
        "/auth/token",
        json={"email": "nobody@example.com", "password": "long-enough-pass"},
    )
    assert limited.status_code == 429


def test_chat_and_upload_rate_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    headers = {"X-User-Id": "u1"}
    assert client.post("/chat", headers=headers).status_code == 200
    assert client.post("/chat", headers=headers).status_code == 200
    assert client.post("/chat", headers=headers).status_code == 429
    assert client.post("/uploads", headers=headers).status_code == 200
    assert client.post("/uploads", headers=headers).status_code == 200
    assert client.post("/uploads", headers=headers).status_code == 429
