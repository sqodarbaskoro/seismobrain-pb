"""
File: test_admin_acl_grants.py
Description: Collection ACL updates must grant live collection_access (FR-ADM-02)
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
from seismobrain_api.app import AppContainer, create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    settings = Settings()  # type: ignore[call-arg]
    return TestClient(
        create_app(
            AppContainer(
                settings=settings,
                metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
                job_queue=InProcessJobQueue(tmp_path / "jobs"),
                object_store=FilesystemObjectStore(tmp_path / "objects"),
                event_log=InMemoryEventLog(),
                rate_limiter=InMemoryRateLimiter(),
                authorization_guard=DenyAllAuthorizationGuard(),
                user_store=InMemoryUserStore(),
            )
        )
    )


def test_set_acl_grants_collection_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    ws = client.post("/admin/workspaces", headers=admin, json={"name": "Ops"})
    workspace_id = ws.json()["id"]
    col = client.post(
        f"/admin/workspaces/{workspace_id}/collections",
        headers=admin,
        json={"name": "Reports"},
    )
    collection_id = col.json()["id"]

    acl = client.put(
        f"/admin/collections/{collection_id}/acl",
        headers=admin,
        json={"entries": [{"principal": "alice", "permission": "read"}]},
    )
    assert acl.status_code == 200

    listed = client.get(
        "/api/v1/collections",
        headers={"X-User-Id": "alice", "X-System-Role": "user"},
    )
    assert listed.status_code == 200
    assert collection_id in listed.json()["collections"]
