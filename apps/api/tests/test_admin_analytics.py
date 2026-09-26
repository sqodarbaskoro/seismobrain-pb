"""
File: test_admin_analytics.py
Description: Analytics usage refusal latency feedback trends (T4.25)
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


def test_analytics_usage_refusal_latency_feedback(
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
    a = container.analytics
    a.record_usage(route="doc_qa", workspace_id="w1")
    a.record_usage(route="doc_qa", workspace_id="w1")
    a.record_refusal("insufficient_evidence")
    a.record_latency(120.0)
    a.record_latency(400.0)
    a.record_unanswered("What is torque?")
    a.record_unanswered("What is torque?")
    a.record_feedback(rating="down", reason="wrong")
    client = TestClient(create_app(container))
    response = client.get(
        "/api/v1/admin/analytics", headers={"X-System-Role": "system_admin"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["usage"]["total"] == 2
    assert body["refusal_mix"]["insufficient_evidence"] == 1
    assert body["latency"]["samples"] == 2
    assert body["top_unanswered_questions"][0]["question"] == "What is torque?"
    assert body["feedback_trends"]["by_rating"]["down"] == 1


def test_analytics_rejects_non_admin_and_anonymous_callers(
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

    anonymous = client.get("/api/v1/admin/analytics")
    assert anonymous.status_code == 401

    member = client.get(
        "/api/v1/admin/analytics",
        headers={"X-User-Id": "bob", "X-System-Role": "user"},
    )
    assert member.status_code == 403
