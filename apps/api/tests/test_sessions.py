"""
File: test_sessions.py
Description: Self-service session list and per-device revoke (T4.5)
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


def test_list_and_revoke_sessions(container: AppContainer) -> None:
    # A "session" is a refresh-token family — created wherever a real login is,
    # not by a dedicated create-session call. Two logins (laptop, phone) here.
    laptop = container.refresh_token_store.issue(
        user_id="u1", ttl_days=30, user_agent="Laptop/Chrome", ip="10.0.0.1"
    )
    container.refresh_token_store.issue(
        user_id="u1", ttl_days=30, user_agent="Phone/Safari", ip="10.0.0.2"
    )

    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}

    listed = client.get("/api/v1/sessions", headers=headers)
    assert listed.status_code == 200
    sessions = listed.json()["sessions"]
    assert {s["user_agent"] for s in sessions} == {"Laptop/Chrome", "Phone/Safari"}

    revoked = client.post(
        f"/api/v1/sessions/{laptop.family_id}/revoke", headers=headers
    )
    assert revoked.json()["revoked"] is True

    after = client.get("/api/v1/sessions", headers=headers)
    remaining = after.json()["sessions"]
    assert len(remaining) == 1
    assert remaining[0]["user_agent"] == "Phone/Safari"


def test_cannot_revoke_someone_elses_session(container: AppContainer) -> None:
    other = container.refresh_token_store.issue(user_id="u2", ttl_days=30)
    client = TestClient(create_app(container))
    response = client.post(
        f"/api/v1/sessions/{other.family_id}/revoke", headers={"X-User-Id": "u1"}
    )
    assert response.status_code == 404


def test_sessions_require_authentication(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    assert client.get("/api/v1/sessions").status_code == 401
