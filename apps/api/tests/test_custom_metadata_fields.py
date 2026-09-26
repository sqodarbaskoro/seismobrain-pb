"""
File: test_custom_metadata_fields.py
Description: Custom metadata fields per workspace (T5.20)
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


def test_custom_fields_filterable_and_trigger_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    client = TestClient(
        create_app(
            AppContainer(
                settings=Settings(),  # type: ignore[call-arg]
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
    response = client.put(
        "/api/v1/workspaces/w1/custom-metadata",
        headers={"X-System-Role": "system_admin"},
        json={"fields": [{"name": "plant", "type": "string", "filterable": True}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["fields"][0]["name"] == "plant"
    assert body["payload_sync_triggered"] is True


def test_custom_metadata_requires_admin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    client = TestClient(
        create_app(
            AppContainer(
                settings=Settings(),  # type: ignore[call-arg]
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
    response = client.put("/api/v1/workspaces/w1/custom-metadata", json={"fields": []})
    assert response.status_code == 401
