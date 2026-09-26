"""
File: test_api_key_route_access.py
Description: Reproduces the API-key route-access gap and specifies T04 behavior (FR-AUTH-07)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-19
Modified: 2026-09-19
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
from seismobrain_api.auth.users import InMemoryUserStore, UserRecord
from seismobrain_api.config import Settings
from seismobrain_core.roles import SystemRole, WorkspaceRole


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    container = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )
    container.collection_access.map_collection("c1", "ws-1")
    container.object_store.put("collections/c1/documents/d1/note.txt", b"Torque is 40 Nm.")
    container.collection_access.add_document(
        document_id="d1",
        collection_id="c1",
        title="Note",
        source_path="note.txt",
        object_key="collections/c1/documents/d1/note.txt",
    )
    container.document_access.map_evidence("e1", "d1")
    container.document_access.map_snapshot("s1", "d1")
    return container


def _owner(container: AppContainer, *, email: str = "owner@example.com") -> UserRecord:
    user = container.user_store.create(
        email=email, name="Owner", password="long-enough-pass", status="active"
    )
    container.collection_access.set_workspace_role(user.id, "ws-1", WorkspaceRole.VIEWER)
    container.collection_access.grant_read(user.id, "c1")
    return user


def _issue_key(
    client: TestClient, owner_id: str, *, scopes: list[str], ttl_seconds: int = 3600
) -> str:
    issued = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": scopes, "ttl_seconds": ttl_seconds},
        headers={"X-User-Id": owner_id},
    )
    assert issued.status_code == 201
    return str(issued.json()["token"])


def _issue_key_bypassing_validation(
    container: AppContainer, owner_id: str, *, scopes: set[str], ttl_seconds: int
) -> str:
    """Simulates a key that predates T04.5's scope/ttl validation (or one issued
    directly by the store) — the HTTP route rejects these inputs outright."""
    _, raw = container.api_tokens.issue(
        owner_id=owner_id, name="legacy", scopes=scopes, ttl_seconds=ttl_seconds
    )
    return raw


def test_gap_valid_read_key_now_lists_collections(container: AppContainer) -> None:
    """Was the confirmed starting-point gap: a valid, unexpired, unrevoked,
    correctly scoped key got 401 because auth/deps.py never recognized sbpat_
    credentials — it only attempted JWT verification. Fixed by T04.4."""
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key(client, owner.id, scopes=["read"])

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/collections",
        "/api/v1/collections/c1/documents",
        "/documents/d1/preview",
        "/documents/d1/download",
        "/citations/e1",
        "/evidence-snapshots/s1",
    ],
)
def test_read_scope_key_allowed_on_supported_routes(container: AppContainer, path: str) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key(client, owner.id, scopes=["read"])

    resp = client.get(path, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_read_scope_key_lists_and_reads_own_conversation(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    created = client.post(
        "/api/v1/conversations",
        json={"workspace_id": "ws-1", "title": "t"},
        headers={"X-User-Id": owner.id},
    )
    assert created.status_code == 201
    conv_id = created.json()["id"]
    token = _issue_key(client, owner.id, scopes=["read"])

    listed = client.get("/api/v1/conversations", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert any(c["id"] == conv_id for c in listed.json()["conversations"])

    messages = client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert messages.status_code == 200


def test_key_without_required_scope_denied(container: AppContainer) -> None:
    """A key with only a legacy/unsupported scope string (the HTTP issue route
    rejects issuing these now — see T04.5) still grants nothing on `read` routes."""
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key_bypassing_validation(container, owner.id, scopes={"other"}, ttl_seconds=3600)

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_client_supplied_required_scope_header_cannot_widen_access(
    container: AppContainer,
) -> None:
    """A caller can't grant itself scope by sending X-Required-Scope; only server
    policy on the route decides what scope is needed."""
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key_bypassing_validation(container, owner.id, scopes={"other"}, ttl_seconds=3600)

    resp = client.get(
        "/api/v1/collections",
        headers={"Authorization": f"Bearer {token}", "X-Required-Scope": "other"},
    )
    assert resp.status_code == 403


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/api/v1/conversations", {"workspace_id": "ws-1", "title": "t"}),
        ("post", "/api/v1/documents/bulk", {"document_ids": ["d1"], "action": "tag"}),
    ],
)
def test_key_denied_on_unsupported_write_routes(
    container: AppContainer, method: str, path: str, json: dict[str, object]
) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key(client, owner.id, scopes=["read"])

    resp = getattr(client, method)(
        path, json=json, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in (401, 403)


def test_key_denied_on_key_management_route_even_for_owner(container: AppContainer) -> None:
    """Key management stays JWT-only, including for the key's own owner."""
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key(client, owner.id, scopes=["read"])

    resp = client.get("/api/v1/api-tokens", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_key_denied_on_admin_route_even_for_admin_owned_key(container: AppContainer) -> None:
    admin = container.user_store.create(
        email="admin@example.com", name="Admin", password="long-enough-pass", status="active"
    )
    container.user_store.set_system_role(admin.id, SystemRole.SYSTEM_ADMIN)
    client = TestClient(create_app(container))
    token = _issue_key(client, admin.id, scopes=["read"])

    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_expired_key_denied(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key_bypassing_validation(container, owner.id, scopes={"read"}, ttl_seconds=-1)

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_revoked_key_denied(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    issued = client.post(
        "/api/v1/api-tokens",
        json={"name": "ci", "scopes": ["read"], "ttl_seconds": 3600},
        headers={"X-User-Id": owner.id},
    )
    token = issued.json()["token"]
    client.post(f"/api/v1/api-tokens/{issued.json()['id']}/revoke", headers={"X-User-Id": owner.id})

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_inactive_owner_denied(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    owner = _owner(container)
    token = _issue_key(client, owner.id, scopes=["read"])
    container.user_store.set_status(owner.id, "disabled")

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_cross_user_object_denial_still_enforced_for_api_keys(container: AppContainer) -> None:
    stranger = container.user_store.create(
        email="stranger@example.com", name="Stranger", password="long-enough-pass", status="active"
    )
    client = TestClient(create_app(container))
    token = _issue_key(client, stranger.id, scopes=["read"])

    resp = client.get("/documents/d1/preview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_jwt_bearer_still_works_on_same_routes(container: AppContainer) -> None:
    """Regression: adding API-key recognition must not disturb the JWT path."""
    client = TestClient(create_app(container))
    reg = client.post(
        "/auth/register",
        json={"email": "jwt@example.com", "password": "long-enough-pass", "name": "J"},
    )
    assert reg.status_code == 201
    login = client.post(
        "/auth/token", json={"email": "jwt@example.com", "password": "long-enough-pass"}
    )
    jwt = login.json()["access_token"]

    resp = client.get("/api/v1/collections", headers={"Authorization": f"Bearer {jwt}"})
    assert resp.status_code == 200
