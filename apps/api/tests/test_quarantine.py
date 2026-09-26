"""
File: test_quarantine.py
Description: Quarantine list/inspect/release, admin-only (T5.15)
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

ADMIN = {"X-System-Role": "system_admin"}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
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


def test_quarantine_list_inspect_and_release(client: TestClient) -> None:
    created = client.post(
        "/api/v1/quarantine", headers=ADMIN, json={"filename": "bad.exe", "reason": "validation"}
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    listed = client.get("/api/v1/quarantine", headers=ADMIN)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [item_id]

    inspected = client.get(f"/api/v1/quarantine/{item_id}", headers=ADMIN)
    assert inspected.json()["status"] == "quarantined"

    released = client.post(f"/api/v1/quarantine/{item_id}/release", headers=ADMIN)
    assert released.json()["status"] == "released"

    # A released item no longer needs review.
    assert client.get("/api/v1/quarantine", headers=ADMIN).json()["items"] == []


def test_quarantine_requires_admin(client: TestClient) -> None:
    assert client.get("/api/v1/quarantine").status_code == 401
    member_headers = {"X-User-Id": "u1", "X-System-Role": "user"}
    response = client.get("/api/v1/quarantine", headers=member_headers)
    assert response.status_code == 403
