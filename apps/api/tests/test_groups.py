"""
File: test_groups.py
Description: Groups many-to-many with collection permissions (T4.1)
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
from seismobrain_core.permissions import Permission


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


def test_groups_membership_and_grants_sync(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-System-Role": "system_admin"}
    created = client.post(
        "/api/v1/groups", json={"name": "engineers"}, headers=headers
    )
    assert created.status_code == 201
    gid = created.json()["id"]
    members = client.post(
        f"/api/v1/groups/{gid}/members",
        json={"user_id": "u1"},
        headers=headers,
    )
    assert "u1" in members.json()["members"]
    grant = client.post(
        f"/api/v1/groups/{gid}/grants",
        json={
            "resource_type": "collection",
            "resource_id": "col-a",
            "permission": "read",
        },
        headers=headers,
    )
    assert grant.json()["vector_sync_ok"] is True
    assert (
        container.groups.permission_for_user(
            "u1", resource_type="collection", resource_id="col-a"
        )
        == Permission.READ
    )
    doc_grant = client.post(
        f"/api/v1/groups/{gid}/grants",
        json={
            "resource_type": "document",
            "resource_id": "doc-1",
            "permission": "write",
        },
        headers=headers,
    )
    assert doc_grant.status_code == 200


def test_list_and_detail_groups(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-System-Role": "system_admin"}
    created = client.post("/api/v1/groups", json={"name": "engineers"}, headers=headers)
    gid = created.json()["id"]
    client.post(f"/api/v1/groups/{gid}/members", json={"user_id": "u1"}, headers=headers)

    listed = client.get("/api/v1/groups", headers=headers)
    assert listed.status_code == 200
    assert any(g["id"] == gid and g["member_count"] == 1 for g in listed.json()["groups"])

    detail = client.get(f"/api/v1/groups/{gid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["members"] == ["u1"]


def test_remove_member_and_revoke_grant(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-System-Role": "system_admin"}
    gid = client.post("/api/v1/groups", json={"name": "engineers"}, headers=headers).json()["id"]
    client.post(f"/api/v1/groups/{gid}/members", json={"user_id": "u1"}, headers=headers)
    client.post(
        f"/api/v1/groups/{gid}/grants",
        json={"resource_type": "collection", "resource_id": "col-a", "permission": "read"},
        headers=headers,
    )

    removed = client.delete(f"/api/v1/groups/{gid}/members/u1", headers=headers)
    assert removed.json()["members"] == []

    grants = client.get(
        "/api/v1/groups/grants",
        params={"resource_type": "collection", "resource_id": "col-a"},
        headers=headers,
    )
    assert grants.status_code == 200
    assert grants.json()["grants"] == [
        {"group_id": gid, "group_name": "engineers", "permission": "read"}
    ]

    revoked = client.delete(
        f"/api/v1/groups/{gid}/grants",
        params={"resource_type": "collection", "resource_id": "col-a"},
        headers=headers,
    )
    assert revoked.json()["revoked"] is True
    after = client.get(
        "/api/v1/groups/grants",
        params={"resource_type": "collection", "resource_id": "col-a"},
        headers=headers,
    )
    assert after.json()["grants"] == []


def test_groups_require_admin(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    assert client.get("/api/v1/groups").status_code == 401
    non_admin = {"X-User-Id": "u1", "X-System-Role": "user"}
    assert client.get("/api/v1/groups", headers=non_admin).status_code == 403
    assert (
        client.post("/api/v1/groups", json={"name": "x"}, headers=non_admin).status_code == 403
    )
