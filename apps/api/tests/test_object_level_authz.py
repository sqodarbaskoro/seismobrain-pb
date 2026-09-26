"""
File: test_object_level_authz.py
Description: Object-level authorization on resource identifiers (SEC-12)
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
from seismobrain_api.app import AppContainer, create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_core.object_authz import ObjectOwnershipStore, ResourceType


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    store = ObjectOwnershipStore()
    for rtype, rid in [
        (ResourceType.CONVERSATION, "c1"),
        (ResourceType.MESSAGE, "m1"),
        (ResourceType.DOCUMENT, "d1"),
        (ResourceType.JOB, "j1"),
        (ResourceType.EVIDENCE, "e1"),
    ]:
        store.put(resource_type=rtype, resource_id=rid, owner_user_id="alice")
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
        object_ownership=store,
    )
    return TestClient(create_app(container))


@pytest.mark.parametrize(
    ("path"),
    [
        "/conversations/c1",
        "/messages/m1",
        "/documents/d1",
        "/jobs/j1",
        "/evidence/e1",
    ],
)
def test_owner_can_access_and_other_user_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    client = _client(tmp_path, monkeypatch)
    ok = client.get(path, headers={"X-User-Id": "alice"})
    assert ok.status_code == 200
    denied = client.get(path, headers={"X-User-Id": "bob"})
    assert denied.status_code == 403
    missing = client.get(path)
    assert missing.status_code == 401
