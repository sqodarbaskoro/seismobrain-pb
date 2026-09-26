"""
File: test_metadata_review_sync.py
Description: Curator metadata review propagates to index (T5.22)
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


def test_metadata_review_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    container.collection_access.add_document(document_id="d1", collection_id="c1", title="Draft")
    client = TestClient(create_app(container))
    response = client.post(
        "/api/v1/metadata/review",
        headers={"X-System-Role": "system_admin"},
        json={"document_id": "d1", "fields": {"title": "Corrected"}},
    )
    assert response.status_code == 200
    assert response.json()["propagated_to_index"] is True
    assert "d1" in container.vector_payload_sync
    assert container.metadata_reviews["d1"]["title"] == "Corrected"
    # The real document catalog is updated too, not just the side log — so the
    # correction actually shows up when browsing/previewing the document.
    assert container.collection_access.get_document("d1")["_meta"].title == "Corrected"


def test_metadata_review_requires_admin_and_real_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    client = TestClient(create_app(container))

    unauthenticated = client.post(
        "/api/v1/metadata/review", json={"document_id": "d1", "fields": {}}
    )
    assert unauthenticated.status_code == 401

    unknown_document = client.post(
        "/api/v1/metadata/review",
        headers={"X-System-Role": "system_admin"},
        json={"document_id": "missing", "fields": {"title": "x"}},
    )
    assert unknown_document.status_code == 404
