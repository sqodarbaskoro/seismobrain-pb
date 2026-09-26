"""
File: test_core_metadata.py
Description: FR-META-01 — core metadata fields filterable in API
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
from seismobrain_core.core_metadata import CORE_METADATA_FIELDS, PUBLIC_METADATA_FIELDS
from seismobrain_core.roles import WorkspaceRole


def test_core_metadata_fields_defined() -> None:
    assert "source_path" in CORE_METADATA_FIELDS
    assert "source_path" not in PUBLIC_METADATA_FIELDS
    for field in (
        "title",
        "doc_type",
        "revision",
        "effective_date",
        "author",
        "language",
        "tags",
    ):
        assert field in PUBLIC_METADATA_FIELDS


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
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
    access.set_workspace_role("viewer", "ws-1", WorkspaceRole.VIEWER)
    access.grant_read("viewer", "col-a")
    access.add_document(
        document_id="doc-1",
        collection_id="col-a",
        title="Pump Manual",
        doc_type="pdf",
        revision="B",
        effective_date="2024-01-15",
        author="Alice",
        language="en",
        tags=("ops", "pump"),
        source_path="/internal/vault/pump.pdf",
    )
    access.add_document(
        document_id="doc-2",
        collection_id="col-a",
        title="Safety Note",
        doc_type="md",
        revision="A",
        effective_date="2023-06-01",
        author="Bob",
        language="en",
        tags=("safety",),
        source_path="/internal/vault/safety.md",
    )
    return container


def test_api_filters_core_metadata_and_hides_source_path(
    container: AppContainer,
) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "viewer"}
    response = client.get(
        "/api/v1/collections/col-a/documents",
        headers=headers,
        params={
            "doc_type": "pdf",
            "revision": "B",
            "author": "Alice",
            "language": "en",
            "effective_date": "2024-01-15",
            "tag": "pump",
        },
    )
    assert response.status_code == 200
    docs = response.json()["documents"]
    assert len(docs) == 1
    doc = docs[0]
    assert doc["id"] == "doc-1"
    assert doc["title"] == "Pump Manual"
    assert doc["revision"] == "B"
    assert doc["author"] == "Alice"
    assert "ops" in doc["tags"]
    assert "source_path" not in doc
