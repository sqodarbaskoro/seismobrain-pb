"""
File: test_chat_doc_qa_provider_fallback.py
Description: Chat must not stick on a dead first LLM provider when another works
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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.chat_doc_qa import run_conversation_doc_qa
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import IndexedHit


@dataclass
class UrlAwareTransport:
    """Fails for Ollama URLs; succeeds for everything else."""

    calls: list[str] = field(default_factory=list)

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append(url)
        if "11434" in url:
            raise ConnectionError("Connection refused")
        return {
            "choices": [
                {"message": {"content": "Flange torque is 40 Nm [E1]."}}
            ],
            "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        }


def test_chat_skips_dead_first_provider_and_uses_working_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    settings = Settings()  # type: ignore[call-arg]
    transport = UrlAwareTransport()
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

    container.admin_catalog.create_provider(
        kind="ollama_vllm",
        name="dead-ollama",
        models=["llama3.2"],
        api_key="local",
        master_key=container.settings.master_key,
        actor="test",
        base_url="http://127.0.0.1:11434/v1",
        locality="local",
    )
    container.admin_catalog.create_provider(
        kind="openai_compatible",
        name="openrouter",
        models=["openai/gpt-4o-mini"],
        api_key="sk-test",
        master_key=container.settings.master_key,
        actor="test",
        base_url="https://openrouter.ai/api/v1",
        locality="external",
    )
    container.search_index.add(
        IndexedHit(
            document_id="doc-1",
            version_id="doc-1:v1",
            text="Flange torque is 40 Nm.",
            collection_id="ops",
            score=1.0,
            metadata={
                "chunk_id": "c1",
                "title": "Ops",
                "section_path": "1",
                "page": 1,
                "extraction_method": "digital",
            },
        )
    )

    result = run_conversation_doc_qa(
        container, question="What is the flange torque?", collection_ids=["ops"]
    )

    assert result.refusal is None
    assert result.answer_text is not None
    assert "40 Nm" in (result.answer_text or "")
    assert any("openrouter.ai" in u for u in transport.calls)
