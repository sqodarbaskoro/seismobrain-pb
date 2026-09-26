"""
File: test_message_controls.py
Description: Stop, regenerate, copy with citations (T3.16)
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
from chat_fixtures import seed_grounded_chat
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


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
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
    seed_grounded_chat(c)
    return c


def test_stop_regenerate_copy(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    conv_id = client.post(
        "/api/v1/conversations", json={"workspace_id": "ws"}, headers=headers
    ).json()["id"]
    stream = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque for P2/94?"},
        headers=headers,
    )
    assert "final" in stream.text
    # Extract message id from store
    conv = container.conversations.get(conv_id)
    assert conv is not None
    assistant = [m for m in conv.messages if m.role == "assistant"][-1]

    stopped = client.post(
        f"/api/v1/conversations/{conv_id}/messages/{assistant.id}/stop",
        headers=headers,
    )
    assert stopped.json()["status"] == "interrupted"

    regen = client.post(
        f"/api/v1/conversations/{conv_id}/messages/{assistant.id}/regenerate",
        headers=headers,
    )
    assert regen.status_code == 200
    assert regen.json()["id"] != assistant.id

    copied = client.get(
        f"/api/v1/conversations/{conv_id}/messages/{assistant.id}/copy",
        headers=headers,
    )
    assert copied.status_code == 200
    assert "Ops Manual" in copied.json()["markdown"]
