"""
File: test_my_workspaces.py
Description: Self-service workspace listing for the chat workspace switcher (FR-CHAT)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-26
Modified: 2026-09-26
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
    settings = Settings()  # type: ignore[call-arg]
    return TestClient(
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


def test_lists_only_workspaces_the_caller_belongs_to(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    alice = {"X-User-Id": "alice", "X-System-Role": "user"}

    ops = client.post("/admin/workspaces", headers=admin, json={"name": "Ops"}).json()
    reports = client.post(
        f"/admin/workspaces/{ops['id']}/collections", headers=admin, json={"name": "Reports"}
    ).json()
    client.put(
        f"/admin/collections/{reports['id']}/acl",
        headers=admin,
        json={"entries": [{"principal": "alice", "permission": "read"}]},
    )
    # A second workspace alice has no role in — must not appear in her listing.
    client.post("/admin/workspaces", headers=admin, json={"name": "Finance"})

    listed = client.get("/api/v1/workspaces", headers=alice)
    assert listed.status_code == 200
    workspaces = listed.json()["workspaces"]
    assert [w["name"] for w in workspaces] == ["Ops"]
    assert workspaces[0]["id"] == ops["id"]
    assert workspaces[0]["collections"] == [{"id": reports["id"], "name": "Reports"}]


def test_admin_sees_every_workspace_via_owner_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    client.post("/admin/workspaces", headers=admin, json={"name": "Ops"})
    client.post("/admin/workspaces", headers=admin, json={"name": "Finance"})

    listed = client.get("/api/v1/workspaces", headers={"X-System-Role": "system_admin"})
    assert listed.status_code == 200
    names = {w["name"] for w in listed.json()["workspaces"]}
    assert names == {"Ops", "Finance"}


def test_caller_with_no_workspace_role_sees_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    client.post("/admin/workspaces", headers=admin, json={"name": "Ops"})

    listed = client.get(
        "/api/v1/workspaces", headers={"X-User-Id": "bob", "X-System-Role": "user"}
    )
    assert listed.status_code == 200
    assert listed.json()["workspaces"] == []
