"""
File: test_document_browse_acl.py
Description: FR-DOC-03 — browse/filter/preview/download limited to entitled collections
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
from seismobrain_core.roles import WorkspaceRole


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
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
    access = container.collection_access
    access.map_collection("col-a", "ws-1")
    access.map_collection("col-b", "ws-1")
    access.set_workspace_role("viewer", "ws-1", WorkspaceRole.VIEWER)
    access.grant_read("viewer", "col-a")
    container.object_store.put("collections/col-a/documents/doc-1/guide.pdf", b"%PDF-fake")
    access.add_document(
        document_id="doc-1",
        collection_id="col-a",
        title="Calibration Guide",
        doc_type="pdf",
        tag="proc",
        source_path="guide.pdf",
        object_key="collections/col-a/documents/doc-1/guide.pdf",
    )
    access.add_document(
        document_id="doc-2",
        collection_id="col-a",
        title="Notes",
        doc_type="txt",
        tag="draft",
    )
    access.add_document(
        document_id="doc-secret",
        collection_id="col-b",
        title="Secret",
        doc_type="pdf",
        tag="proc",
    )
    return container


def test_viewer_sees_only_entitled_collections(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.get("/api/v1/collections", headers={"X-User-Id": "viewer"})
    assert response.status_code == 200
    assert response.json()["collections"] == ["col-a"]


def test_browse_filter_preview_download_entitled_only(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "viewer"}

    denied = client.get("/api/v1/collections/col-b/documents", headers=headers)
    assert denied.status_code == 403

    listed = client.get(
        "/api/v1/collections/col-a/documents",
        headers=headers,
        params={"q": "Calibration", "doc_type": "pdf", "tag": "proc"},
    )
    assert listed.status_code == 200
    docs = listed.json()["documents"]
    assert [doc["id"] for doc in docs] == ["doc-1"]

    assert client.get("/documents/doc-1/preview", headers=headers).status_code == 200
    assert client.get("/documents/doc-1/download", headers=headers).status_code == 200
    assert client.get("/documents/doc-secret/preview", headers=headers).status_code == 403
