"""
File: test_sse_replay.py
Description: Conversation message SSE streaming and EventLog replay (T3.13)
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


def _parse_sse(raw: str) -> list[tuple[str, str, str]]:
    events: list[tuple[str, str, str]] = []
    blocks = [b for b in raw.split("\n\n") if b.strip()]
    for block in blocks:
        eid = ""
        etype = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("id: "):
                eid = line[4:]
            elif line.startswith("event: "):
                etype = line[7:]
            elif line.startswith("data: "):
                data = line[6:]
        events.append((eid, etype, data))
    return events


def test_sse_stream_and_replay_across_stateless_client(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    created = client.post(
        "/api/v1/conversations", json={"workspace_id": "ws1"}, headers=headers
    )
    assert created.status_code == 201
    conv_id = created.json()["id"]

    first = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque for P2/94?"},
        headers=headers,
    )
    assert first.status_code == 200
    assert "text/event-stream" in first.headers["content-type"]
    events = _parse_sse(first.text)
    assert any(etype == "status" for _, etype, _ in events)
    assert any(etype == "sentence" for _, etype, _ in events)
    assert any(etype == "final" for _, etype, _ in events)
    last_id = events[-1][0]

    # Simulate reconnect to another replica with Last-Event-ID (shared EventLog).
    replay = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "ignored-on-replay"},
        headers={**headers, "Last-Event-ID": last_id},
    )
    assert replay.status_code == 200
    # After last event, replay may be empty → finalized message from store.
    replay_events = _parse_sse(replay.text)
    assert replay_events
    assert replay_events[0][1] in {"final", "interrupted"}
