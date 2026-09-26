"""
File: test_ingest_job_status_route.py
Description: Self-service per-stage ingest progress for the Documents page's own
    upload — anyone who can read the collection, not just admins (FR-DOC-01)
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
from seismobrain_api.app import create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.starter_ingest import register_starter_ingest
from seismobrain_core.roles import WorkspaceRole


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    c = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )
    register_starter_ingest(c)
    c.collection_access.map_collection("col1", "ws1")
    c.collection_access.set_workspace_role("alice", "ws1", WorkspaceRole.OWNER)
    c.collection_access.grant_write("alice", "col1")
    return c


def test_uploader_can_poll_their_own_upload_to_completion(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    content = b"# Flange\n\nTorque for flange P2/94 is 40 Nm.\n"
    uploaded = client.post(
        "/api/v1/collections/col1/documents",
        headers=headers,
        files={"file": ("note.md", content, "text/markdown")},
    )
    assert uploaded.status_code == 200
    job_id = uploaded.json()["job_id"]

    container.job_queue.run_pending(timeout_seconds=5)

    status = client.get(f"/api/v1/collections/col1/jobs/{job_id}", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["stage"] == "READY"
    assert body["status"] == "succeeded"
    assert body["error"] is None


def test_a_non_member_cannot_poll_the_job(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    uploaded = client.post(
        "/api/v1/collections/col1/documents",
        headers={"X-User-Id": "alice"},
        files={"file": ("note.md", b"hello", "text/plain")},
    )
    job_id = uploaded.json()["job_id"]

    status = client.get(
        f"/api/v1/collections/col1/jobs/{job_id}", headers={"X-User-Id": "mallory"}
    )
    assert status.status_code == 403


def test_a_job_id_from_another_collection_is_not_found(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    container.collection_access.map_collection("col2", "ws1")
    container.collection_access.grant_write("alice", "col2")
    uploaded = client.post(
        "/api/v1/collections/col1/documents",
        headers=headers,
        files={"file": ("note.md", b"hello", "text/plain")},
    )
    job_id = uploaded.json()["job_id"]

    status = client.get(f"/api/v1/collections/col2/jobs/{job_id}", headers=headers)
    assert status.status_code == 404
