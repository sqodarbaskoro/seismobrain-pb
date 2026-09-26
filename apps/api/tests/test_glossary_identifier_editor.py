"""
File: test_glossary_identifier_editor.py
Description: Glossary and identifier-pattern editor (T5.29)
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

ADMIN = {"X-System-Role": "system_admin"}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    return TestClient(
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


def test_glossary_and_identifier_pattern_editor(client: TestClient) -> None:
    ws = "ws-1"
    g = client.put(
        f"/api/v1/workspaces/{ws}/glossary",
        headers=ADMIN,
        json={"entries": [{"term": "PPE", "expansion": "personal protective equipment"}]},
    )
    assert g.status_code == 200
    assert g.json()["glossary"][0]["term"] == "PPE"

    p = client.put(
        f"/api/v1/workspaces/{ws}/identifier-patterns",
        headers=ADMIN,
        json={
            "patterns": [
                {"name": "flange", "pattern": r"P\d+/\d+", "confidence": "high"}
            ]
        },
    )
    assert p.status_code == 200
    assert p.json()["identifier_patterns"][0]["name"] == "flange"

    got = client.get(f"/api/v1/workspaces/{ws}/glossary", headers=ADMIN)
    assert got.status_code == 200
    assert len(got.json()["glossary"]) == 1
    assert len(got.json()["identifier_patterns"]) == 1


def test_glossary_requires_admin(client: TestClient) -> None:
    assert client.get("/api/v1/workspaces/ws-1/glossary").status_code == 401
    assert (
        client.put(
            "/api/v1/workspaces/ws-1/glossary",
            headers={"X-User-Id": "u1", "X-System-Role": "user"},
            json={"entries": []},
        ).status_code
        == 403
    )
