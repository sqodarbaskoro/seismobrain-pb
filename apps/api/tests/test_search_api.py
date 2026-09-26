"""
File: test_search_api.py
Description: Retrieval search API with ACL and guard (T4.11)
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
from seismobrain_api.search_index import IndexedHit


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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
    container.search_index.add(
        IndexedHit(
            document_id="d-ok",
            version_id="v1",
            text="pump seal procedure",
            collection_id="c1",
            score=1.0,
        )
    )
    container.search_index.add(
        IndexedHit(
            document_id="d-denied",
            version_id="v1",
            text="pump seal secret",
            collection_id="c1",
            score=0.9,
        )
    )
    container.document_access.grant("u1", "d-ok")
    return TestClient(create_app(container))


def test_search_api_enforces_acl_and_guard(client: TestClient) -> None:
    response = client.post(
        "/api/v1/search",
        headers={"X-User-Id": "u1"},
        json={"query": "pump seal", "collection_ids": ["c1"], "filters": {}},
    )
    assert response.status_code == 200
    body = response.json()
    ids = [h["document_id"] for h in body["hits"]]
    assert ids == ["d-ok"]
    assert body["guard"]["dropped"] == 1
