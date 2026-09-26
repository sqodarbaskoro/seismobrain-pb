"""
File: test_conversation_followup_context.py
Description: Follow-up questions must resolve pronouns against conversation
    history before retrieval, not drift onto an unrelated document (FR-QRY-04)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.1.1
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
from seismobrain_api.app import create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import IndexedHit


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
        llm_transport=RecordingTransport(
            response={
                "choices": [
                    {
                        "message": {
                            "content": "SYNCKIT runs three solver processes. [E1]",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 8},
            }
        ),
    )
    c.admin_catalog.create_provider(
        kind="openai_compatible",
        name="test-llm",
        models=["test-model"],
        api_key="sk-test",
        master_key=c.settings.master_key,
        actor="test",
        base_url="https://openrouter.ai/api/v1",
        locality="external",
    )
    # Route-Guide has a higher static relevance score, so an un-rewritten follow-up
    # with no discriminative keywords ("How does it work?") falls back to
    # ranking it first (search_index.py's no-token-match fallback sorts by
    # this raw .score) unless the rewrite pulls "SYNCKIT" in from history.
    c.search_index.add(
        IndexedHit(
            document_id="routeguide-doc",
            version_id="routeguide-doc:v1",
            text="Route-Guide manages fleet routing and collision avoidance.",
            collection_id="ops",
            score=0.99,
            metadata={"title": "Route-Guide Manual", "chunk_id": "routeguide-c1"},
        )
    )
    c.search_index.add(
        IndexedHit(
            document_id="synckit-doc",
            version_id="synckit-doc:v1",
            text="SYNCKIT stands for Synchronized Process Control.",
            collection_id="ops",
            score=0.5,
            metadata={"title": "SYNCKIT Manual", "chunk_id": "synckit-c1"},
        )
    )
    return c


def test_pronoun_followup_retrieves_prior_topic_not_unrelated_doc(
    container: AppContainer,
) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    conv_id = client.post(
        "/api/v1/conversations", json={"workspace_id": "ws"}, headers=headers
    ).json()["id"]

    first = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is SYNCKIT?", "scope": {"collections": ["ops"]}},
        headers=headers,
    )
    assert "SYNCKIT Manual" in first.text
    assert "Route-Guide Manual" not in first.text

    followup = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "How does it work?", "scope": {"collections": ["ops"]}},
        headers=headers,
    )
    assert "SYNCKIT Manual" in followup.text
    assert "Route-Guide Manual" not in followup.text

    # The transcript still stores the user's literal words, not the rewrite.
    conv = container.conversations.get(conv_id)
    assert conv is not None
    user_turns = [m.content for m in conv.messages if m.role == "user"]
    assert user_turns == ["What is SYNCKIT?", "How does it work?"]


@pytest.mark.parametrize("topic", ["synckit", "SYNCKIT"])
def test_three_question_sequence_keeps_topic_in_retrieval_and_actual_prompt(
    container: AppContainer, topic: str
) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    conv_id = client.post(
        "/api/v1/conversations", json={"workspace_id": "ws"}, headers=headers
    ).json()["id"]
    questions = [f"what is {topic}", "where this is started?", "how can we started?"]
    for question in questions:
        response = client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": question, "scope": {"collections": ["ops"]}},
            headers=headers,
        )
        assert response.status_code == 200
        assert "SYNCKIT Manual" in response.text
        assert "Route-Guide Manual" not in response.text

    transport = container.llm_transport
    assert isinstance(transport, RecordingTransport)
    assert len(transport.calls) == 3
    prompt = transport.calls[-1]["body"]["messages"][-1]["content"]
    resolved_question = prompt.split("<question>\n")[1].split("\n</question>")[0]
    assert topic in resolved_question
    assert questions[-1] in resolved_question
    history = prompt.split("<history_summary>\n")[1].split("\n</history_summary>")[0]
    assert f"user: {questions[0]}" in history
    assert f"user: {questions[1]}" in history
    assert "assistant: SYNCKIT" in history

    conv = container.conversations.get(conv_id)
    assert conv is not None
    assert [m.content for m in conv.messages if m.role == "user"] == questions


def test_new_conversation_does_not_inherit_another_conversations_topic(
    container: AppContainer,
) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "u1"}
    for question in ["What is SYNCKIT?", "What is Route-Guide?"]:
        conv_id = client.post(
            "/api/v1/conversations", json={"workspace_id": "ws"}, headers=headers
        ).json()["id"]
        client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": question, "scope": {"collections": ["ops"]}},
            headers=headers,
        )
    transport = container.llm_transport
    assert isinstance(transport, RecordingTransport)
    prompt = transport.calls[-1]["body"]["messages"][-1]["content"]
    assert "<history_summary>\n\n</history_summary>" in prompt
    assert "SYNCKIT" not in prompt
