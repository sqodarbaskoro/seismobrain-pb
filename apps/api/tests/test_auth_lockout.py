"""
File: test_auth_lockout.py
Description: Account lockout with progressive delay after failed logins (FR-AUTH-08)
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
from seismobrain_api.auth.lockout import AccountLockout
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings


class _Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lockout: AccountLockout
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("REGISTRATION_MODE", "open")
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
        account_lockout=lockout,
    )
    return TestClient(create_app(container), base_url="https://testserver")


def test_progressive_delay_blocks_brute_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = _Clock()
    lockout = AccountLockout(clock=clock)
    client = _client(tmp_path, monkeypatch, lockout)
    client.post(
        "/auth/register",
        json={"email": "u@example.com", "password": "long-enough-pass", "name": "U"},
    )
    # First failures are accepted as 401 without lockout delay.
    for _ in range(3):
        resp = client.post(
            "/auth/token",
            json={"email": "u@example.com", "password": "wrong-password!!"},
        )
        assert resp.status_code == 401

    # Next attempt is locked with progressive delay.
    locked = client.post(
        "/auth/token",
        json={"email": "u@example.com", "password": "wrong-password!!"},
    )
    assert locked.status_code == 429
    assert int(locked.headers["Retry-After"]) >= 1

    # Still locked before delay elapses.
    still = client.post(
        "/auth/token",
        json={"email": "u@example.com", "password": "long-enough-pass"},
    )
    assert still.status_code == 429

    clock.advance(float(locked.headers["Retry-After"]))
    ok = client.post(
        "/auth/token",
        json={"email": "u@example.com", "password": "long-enough-pass"},
    )
    assert ok.status_code == 200
