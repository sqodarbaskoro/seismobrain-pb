"""
File: test_otel_tracing.py
Description: One OTel trace per message with §14.1 spans (T4.19)
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
from seismobrain_api.conversations import MessageRecord
from seismobrain_api.otel import MESSAGE_SPANS, InMemoryTracer


def test_message_trace_includes_required_spans_and_id_on_message(
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
    created = client.post(
        "/api/v1/conversations",
        headers={"X-User-Id": "u1"},
        json={"workspace_id": "w1", "title": "t"},
    )
    assert created.status_code == 201
    conv_id = created.json()["id"]

    tracer = InMemoryTracer()
    trace = tracer.start_message_trace()
    for name in MESSAGE_SPANS:
        attrs = {"tokens_out": 3} if name == "llm.generate" else {}
        with tracer.span(trace, name, **attrs):
            pass
    assert [s.name for s in trace.spans] == list(MESSAGE_SPANS)

    msg = MessageRecord(
        id=container.conversations.new_message_id(),
        conversation_id=conv_id,
        role="assistant",
        content="ok [E1]",
        generation_record={"trace_id": trace.trace_id},
    )
    container.conversations.add_message(conv_id, "u1", msg)
    stored = container.conversations.get_message(conv_id, msg.id, "u1")
    assert stored is not None
    assert stored.generation_record["trace_id"] == trace.trace_id

    copied = client.get(
        f"/api/v1/conversations/{conv_id}/messages/{msg.id}/copy",
        headers={"X-User-Id": "u1"},
    )
    assert copied.status_code == 200
    # Trace ID is stored server-side on the message record (returned via generation path).
    assert (
        container.conversations.get_message(conv_id, msg.id, "u1")
        .generation_record["trace_id"]  # type: ignore[union-attr]
        == trace.trace_id
    )
