"""
File: test_upload_size_limit.py
Description: FR-DOC-01 — streamed multipart upload size limit; oversize rejected before full read
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

from collections.abc import Iterator
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
from seismobrain_api.upload_limits import UploadTooLargeError, read_limited_chunks
from seismobrain_core.roles import WorkspaceRole


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("UPLOAD_MAX_BYTES", "1024")
    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def container(tmp_path: Path, settings: Settings) -> AppContainer:
    return AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )


def test_read_limited_chunks_stops_before_consuming_remaining() -> None:
    consumed: list[int] = []

    def chunks() -> Iterator[bytes]:
        for index, payload in enumerate((b"a" * 100, b"b" * 100, b"c" * 10_000)):
            consumed.append(index)
            yield payload

    with pytest.raises(UploadTooLargeError) as excinfo:
        read_limited_chunks(chunks(), max_bytes=150)
    assert excinfo.value.bytes_read == 200
    assert consumed == [0, 1]


def test_upload_within_limit_enqueues_for_writer(container: AppContainer) -> None:
    container.collection_access.map_collection("col-1", "ws-1")
    container.collection_access.set_workspace_role("u1", "ws-1", WorkspaceRole.MEMBER)
    container.collection_access.grant_write("u1", "col-1")
    client = TestClient(create_app(container))
    response = client.post(
        "/api/v1/collections/col-1/documents",
        headers={"X-User-Id": "u1"},
        files={"file": ("note.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert body["job_id"]
    assert container.job_queue.get_status(body["job_id"]) == "pending"


def test_oversize_upload_rejected_with_413(container: AppContainer) -> None:
    container.collection_access.map_collection("col-1", "ws-1")
    container.collection_access.set_workspace_role("u1", "ws-1", WorkspaceRole.CURATOR)
    client = TestClient(create_app(container))
    response = client.post(
        "/api/v1/collections/col-1/documents",
        headers={"X-User-Id": "u1"},
        files={"file": ("big.bin", b"x" * 2048, "application/octet-stream")},
    )
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert detail["code"] == "upload_too_large"
    assert detail["max_bytes"] == 1024
    assert detail["bytes_read"] <= 1024 + 64 * 1024


def test_viewer_without_write_denied(container: AppContainer) -> None:
    container.collection_access.map_collection("col-1", "ws-1")
    container.collection_access.set_workspace_role("u2", "ws-1", WorkspaceRole.VIEWER)
    client = TestClient(create_app(container))
    response = client.post(
        "/api/v1/collections/col-1/documents",
        headers={"X-User-Id": "u2"},
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 403
