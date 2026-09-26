"""
File: test_admin_providers_openrouter.py
Description: Provider strategy fields and connection test for OpenAI-compatible (OpenRouter)
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
from seismobrain_adapters.llm.transport import RecordingTransport
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import AppContainer, create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings


def _client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, transport: RecordingTransport
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
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
        llm_transport=transport,
    )
    return TestClient(create_app(container))


def test_create_openai_compatible_provider_with_base_url_and_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = RecordingTransport(
        response={
            "choices": [{"message": {"content": "pong"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    client = _client(tmp_path, monkeypatch, transport=transport)
    admin = {"X-System-Role": "system_admin"}
    created = client.post(
        "/admin/providers",
        headers=admin,
        json={
            "kind": "openai_compatible",
            "name": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "models": ["openai/gpt-4o-mini"],
            "api_key": "sk-or-test",
            "locality": "external",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["kind"] == "openai_compatible"
    assert body["base_url"] == "https://openrouter.ai/api/v1"
    assert body["locality"] == "external"
    assert body["models"] == ["openai/gpt-4o-mini"]
    assert "api_key" not in body

    test = client.post(f"/admin/providers/{body['id']}/test", headers=admin)
    assert test.status_code == 200
    assert test.json()["ok"] is True
    assert transport.calls
    assert transport.calls[0]["url"] == "https://openrouter.ai/api/v1/chat/completions"
