"""
File: test_bulk_document_actions.py
Description: Bulk move/retag/delete/re-index against the real catalog, audited (T5.18)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.3.0
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
from seismobrain_api.search_index import IndexedHit
from seismobrain_core.roles import WorkspaceRole


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
    container.collection_access.map_collection("c2", "ws-1")
    container.collection_access.add_document(document_id="d1", collection_id="c1", title="A")
    container.collection_access.add_document(document_id="d2", collection_id="c1", title="B")
    return container


def _grant_curator(container: AppContainer, user_id: str) -> None:
    container.collection_access.set_workspace_role("curator", "ws-1", WorkspaceRole.CURATOR)
    container.collection_access.grant_write("curator", "c1")
    container.collection_access.grant_write("curator", "c2")
    _ = user_id  # kept for readability at call sites


def test_bulk_move_mutates_real_catalog_and_is_audited(container: AppContainer) -> None:
    _grant_curator(container, "curator")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["d1", "d2"], "action": "move", "target_collection_id": "c2"},
    )

    assert response.status_code == 200
    assert response.json() == {"action": "move", "count": 2}
    assert container.collection_access.get_document("d1")["collection_id"] == "c2"
    assert container.collection_access.get_document("d2")["collection_id"] == "c2"
    assert any(a.action == "documents.bulk.move" for a in container.admin_catalog.audit)


def test_bulk_move_re_scopes_indexed_chunks(container: AppContainer) -> None:
    """T7.30: a moved document's chunks must follow it, or they stay ACL-scoped to
    the collection it was moved out of."""
    container.search_index.add(
        IndexedHit(
            document_id="d1",
            version_id="d1:v1",
            text="Torque for flange P2/94 is 40 Nm.",
            collection_id="c1",
            score=1.0,
            metadata={"chunk_id": "d1:chunk-1"},
        )
    )
    _grant_curator(container, "curator")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["d1"], "action": "move", "target_collection_id": "c2"},
    )

    assert response.status_code == 200
    hits = [h for h in container.search_index.hits if h.document_id == "d1"]
    assert hits and all(h.collection_id == "c2" for h in hits)


def test_bulk_retag_and_delete(container: AppContainer) -> None:
    _grant_curator(container, "curator")
    client = TestClient(create_app(container))

    retagged = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["d1"], "action": "retag", "tags": ["urgent"]},
    )
    assert retagged.status_code == 200
    assert container.collection_access.get_document("d1")["tag"] == "urgent"

    deleted = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["d1"], "action": "delete"},
    )
    assert deleted.status_code == 200
    assert container.collection_access.get_document("d1")["deleted"] is True
    # A deleted document no longer shows up in browse results (d2 still does).
    ids = {doc["id"] for doc in container.collection_access.list_documents("curator", "c1")}
    assert ids == {"d2"}


def test_bulk_action_requires_write_permission(container: AppContainer) -> None:
    container.collection_access.set_workspace_role("viewer", "ws-1", WorkspaceRole.VIEWER)
    container.collection_access.grant_read("viewer", "c1")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "viewer"},
        json={"document_ids": ["d1"], "action": "delete"},
    )

    assert response.status_code == 403
    assert container.collection_access.get_document("d1")["deleted"] is False


def test_bulk_move_requires_write_on_destination_collection(container: AppContainer) -> None:
    # Curator can write c1 (source) but not c3 (destination) — the move must be denied.
    container.collection_access.map_collection("c3", "ws-2")
    container.collection_access.set_workspace_role("curator", "ws-1", WorkspaceRole.CURATOR)
    container.collection_access.grant_write("curator", "c1")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["d1"], "action": "move", "target_collection_id": "c3"},
    )

    assert response.status_code == 403
    assert container.collection_access.get_document("d1")["collection_id"] == "c1"


def test_bulk_action_unknown_document_is_404(container: AppContainer) -> None:
    _grant_curator(container, "curator")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/documents/bulk",
        headers={"X-User-Id": "curator"},
        json={"document_ids": ["missing"], "action": "delete"},
    )

    assert response.status_code == 404
