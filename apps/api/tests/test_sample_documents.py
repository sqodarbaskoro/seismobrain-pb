"""
File: test_sample_documents.py
Description: Admin-only bundled sample corpus loader for guided setup (FR-DOC-01, M1 onboarding)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
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
from seismobrain_core.roles import WorkspaceRole


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


def test_admin_loads_bundled_sample_corpus_into_a_collection(
    container: AppContainer,
) -> None:
    container.collection_access.map_collection("col-1", "ws-1")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/collections/col-1/sample-documents",
        headers={"X-System-Role": "system_admin"},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["documents"]) >= 1
    for doc in body["documents"]:
        assert doc["document_id"]
        assert doc["job_id"]
        assert container.job_queue.get_status(doc["job_id"]) == "pending"
        assert container.object_store.get(doc["object_key"])


def test_non_admin_cannot_load_sample_documents(container: AppContainer) -> None:
    container.collection_access.map_collection("col-1", "ws-1")
    container.collection_access.set_workspace_role("u1", "ws-1", WorkspaceRole.OWNER)
    container.collection_access.grant_write("u1", "col-1")
    client = TestClient(create_app(container))

    response = client.post(
        "/api/v1/collections/col-1/sample-documents",
        headers={"X-User-Id": "u1", "X-System-Role": "user"},
    )

    assert response.status_code == 403


def test_unauthenticated_cannot_load_sample_documents(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.post("/api/v1/collections/col-1/sample-documents")
    assert response.status_code == 401
