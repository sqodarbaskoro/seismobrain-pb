"""
File: test_chat_analytics_recording.py
Description: Chat and feedback flows must feed AnalyticsStore, not just the admin
    console's own routes — GET /api/v1/admin/analytics was previously always empty
    because nothing in the real request path ever recorded into it (FR-ADM-08)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-26
Modified: 2026-09-26
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
    return AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )


def test_answered_chat_message_records_usage_and_latency(container: AppContainer) -> None:
    seed_grounded_chat(container)
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]

    client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque?"},
        headers=headers,
    )

    snapshot = container.analytics.snapshot()
    assert snapshot["usage"]["total"] == 1
    assert snapshot["latency"]["samples"] == 1
    assert snapshot["latency"]["p95_ms"] >= 0


def test_refused_chat_message_records_refusal_and_unanswered_question(
    container: AppContainer,
) -> None:
    # No provider configured -> provider_error refusal (same path a real "nothing
    # matched" or "LLM unreachable" refusal takes).
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]

    client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque?"},
        headers=headers,
    )

    snapshot = container.analytics.snapshot()
    assert snapshot["usage"]["total"] == 1
    assert snapshot["refusal_mix"]["provider_error"] == 1
    assert snapshot["top_unanswered_questions"][0]["question"] == "What is torque?"


def test_feedback_endpoint_records_into_analytics(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    response = client.post(
        "/api/v1/feedback",
        json={"message_id": "m1", "rating": "down", "reason": "wrong_citation"},
        headers={"X-User-Id": "alice"},
    )
    assert response.status_code == 201

    snapshot = container.analytics.snapshot()
    assert snapshot["feedback_trends"]["by_rating"]["down"] == 1
    assert snapshot["feedback_trends"]["by_reason"]["wrong_citation"] == 1
