"""
File: test_guard_resource_access.py
Description: Preview/download/citation/snapshot follow real collection ACL (FR-ACL-10)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.3.1
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
    container.collection_access.set_workspace_role("alice", "ws-1", WorkspaceRole.VIEWER)
    container.collection_access.grant_read("alice", "c1")
    return container


@pytest.mark.parametrize(
    "path",
    [
        "/documents/d1/preview",
        "/documents/d1/download",
        "/citations/e1",
        "/evidence-snapshots/s1",
    ],
)
def test_revoked_reader_loses_access_immediately(container: AppContainer, path: str) -> None:
    client = TestClient(create_app(container))
    assert client.get(path, headers={"X-User-Id": "alice"}).status_code == 200

    container.collection_access.revoke_read("alice", "c1")
    assert client.get(path, headers={"X-User-Id": "alice"}).status_code == 403


def test_stranger_never_had_access(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.get("/documents/d1/preview", headers={"X-User-Id": "mallory"})
    assert response.status_code == 403


def test_preview_returns_real_text(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.get("/documents/d1/preview", headers={"X-User-Id": "alice"})
    assert response.status_code == 200
    body = response.json()
    assert "40 Nm" in body["text"]
    assert body["best_effort"] is False  # .txt is a real text-like format


def test_preview_extracts_pdf_text_not_raw_bytes(
    container: AppContainer, tmp_path: Path
) -> None:
    fixture = (
        Path(__file__).parent.parent.parent.parent
        / "packages/ingest/tests/fixtures/device_controller_real.pdf"
    )
    key = "collections/c1/documents/d-pdf/device.pdf"
    container.object_store.put(key, fixture.read_bytes())
    container.collection_access.add_document(
        document_id="d-pdf",
        collection_id="c1",
        title="Device Controller",
        source_path="device.pdf",
        object_key=key,
        doc_type="pdf",
    )
    client = TestClient(create_app(container))
    response = client.get("/documents/d-pdf/preview", headers={"X-User-Id": "alice"})
    assert response.status_code == 200
    body = response.json()
    assert not body["text"].startswith("%PDF")
    assert "Device Controller monitors sensor volt levels." in body["text"]
    assert body["best_effort"] is False


def test_download_streams_real_bytes(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.get("/documents/d1/download", headers={"X-User-Id": "alice"})
    assert response.status_code == 200
    assert response.content == b"Torque is 40 Nm."
    assert "note.txt" in response.headers["content-disposition"]


def test_system_admin_bypasses_collection_grant(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.get(
        "/documents/d1/preview",
        headers={"X-User-Id": "root", "X-System-Role": "system_admin"},
    )
    assert response.status_code == 200
