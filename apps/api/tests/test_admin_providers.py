"""
File: test_admin_providers.py
Description: Provider configuration shell with encrypted secrets (FR-ADM-04)
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
from seismobrain_adapters.llm.transport import RecordingTransport
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import AppContainer, create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_core.envelope import EnvelopeCipher


def _admin_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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


def test_provider_config_encrypts_secret_and_tests_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _admin_client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    created = client.post(
        "/admin/providers",
        headers=admin,
        json={
            "kind": "ollama_vllm",
            "name": "local-llm",
            "base_url": "http://127.0.0.1:11434/v1",
            "models": ["tiny-chat"],
            "api_key": "sk-test-secret",
            "locality": "local",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert "api_key" not in body
    assert body["secret_key_id"]
    assert body["has_secret"] is True
    assert body["base_url"] == "http://127.0.0.1:11434/v1"
    assert body["kind"] == "ollama_vllm"
    container = client.app.state.container
    container.llm_transport = RecordingTransport(
        response={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    test = client.post(f"/admin/providers/{body['id']}/test", headers=admin)
    assert test.status_code == 200
    assert test.json()["ok"] is True


def test_update_provider_fields_and_optional_secret_rotation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _admin_client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    created = client.post(
        "/admin/providers",
        headers=admin,
        json={
            "kind": "openai_compatible",
            "name": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "models": ["openai/gpt-4o-mini"],
            "api_key": "sk-original",
            "locality": "external",
        },
    )
    assert created.status_code == 201
    provider_id = created.json()["id"]
    container = client.app.state.container

    keep_secret = client.put(
        f"/admin/providers/{provider_id}",
        headers=admin,
        json={
            "kind": "openai_compatible",
            "name": "OpenRouter (renamed)",
            "base_url": "https://openrouter.ai/api/v1",
            "models": ["deepseek/deepseek-v4.1-flash"],
            "locality": "external",
        },
    )
    assert keep_secret.status_code == 200, keep_secret.text
    body = keep_secret.json()
    assert body["name"] == "OpenRouter (renamed)"
    assert body["models"] == ["deepseek/deepseek-v4.1-flash"]
    assert "api_key" not in body
    record = container.admin_catalog.get_provider(provider_id)
    assert record is not None
    plain = EnvelopeCipher(
        master_key=container.settings.master_key, key_id=record.secret.key_id
    ).decrypt(record.secret)
    assert plain == b"sk-original"

    rotate = client.put(
        f"/admin/providers/{provider_id}",
        headers=admin,
        json={
            "kind": "openai_compatible",
            "name": "OpenRouter (renamed)",
            "base_url": "https://openrouter.ai/api/v1",
            "models": ["deepseek/deepseek-v4.1-flash"],
            "locality": "external",
            "api_key": "sk-rotated",
        },
    )
    assert rotate.status_code == 200
    record = container.admin_catalog.get_provider(provider_id)
    assert record is not None
    plain = EnvelopeCipher(
        master_key=container.settings.master_key, key_id=record.secret.key_id
    ).decrypt(record.secret)
    assert plain == b"sk-rotated"
    actions = [e.action for e in container.admin_catalog.audit]
    assert "provider.update" in actions


def test_delete_provider_removes_from_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _admin_client(tmp_path, monkeypatch)
    admin = {"X-System-Role": "system_admin"}
    created = client.post(
        "/admin/providers",
        headers=admin,
        json={
            "kind": "ollama_vllm",
            "name": "local-llm",
            "base_url": "http://127.0.0.1:11434/v1",
            "models": ["llama3.2"],
            "api_key": "ollama",
            "locality": "local",
        },
    )
    provider_id = created.json()["id"]
    deleted = client.delete(f"/admin/providers/{provider_id}", headers=admin)
    assert deleted.status_code == 204
    listed = client.get("/admin/providers", headers=admin)
    assert listed.status_code == 200
    assert listed.json()["providers"] == []
    missing = client.delete(f"/admin/providers/{provider_id}", headers=admin)
    assert missing.status_code == 404
