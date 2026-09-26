"""
File: test_research_enable_audit.py
Description: Research disabled by default; enabling audited (T5.6)
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


def test_research_disabled_by_default_enable_audited(
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
    admin = {"X-System-Role": "system_admin", "X-User-Id": "admin"}
    ws = client.post("/admin/workspaces", headers=admin, json={"name": "Ops"})
    assert ws.status_code == 201
    workspace_id = ws.json()["id"]
    assert container.admin_catalog.workspaces[workspace_id].research_enabled is False

    denied = client.post(
        "/api/v1/research/stream",
        headers={"X-User-Id": "u1"},
        json={"question": "torque", "workspace_id": workspace_id},
    )
    assert denied.status_code == 403

    non_admin_attempt = client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/research",
        headers={"X-User-Id": "u1", "X-System-Role": "user"},
        json={"enabled": True},
    )
    assert non_admin_attempt.status_code == 403
    assert container.admin_catalog.workspaces[workspace_id].research_enabled is False

    enabled = client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/research",
        headers=admin,
        json={"enabled": True},
    )
    assert enabled.json()["research_enabled"] is True
    actions = [e.action for e in container.admin_catalog.audit]
    assert "workspace.research.enable" in actions
