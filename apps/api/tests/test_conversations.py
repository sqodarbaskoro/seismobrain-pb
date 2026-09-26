"""
File: test_conversations.py
Description: Conversations CRUD with ownership enforcement (T3.14)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.3.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
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
from seismobrain_api.conversations import ConversationStore, MessageRecord, title_from_question


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


def test_conversation_crud_ownership(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    a = {"X-User-Id": "alice"}
    b = {"X-User-Id": "bob"}
    created = client.post(
        "/api/v1/conversations",
        json={"workspace_id": "ws", "title": "Torque"},
        headers=a,
    )
    assert created.status_code == 201
    conv_id = created.json()["id"]
    assert conv_id.startswith("conv_")

    listed = client.get("/api/v1/conversations", headers=a)
    assert any(c["id"] == conv_id for c in listed.json()["conversations"])
    assert client.get("/api/v1/conversations", headers=b).json()["conversations"] == []

    renamed = client.patch(
        f"/api/v1/conversations/{conv_id}", json={"title": "Flange"}, headers=a
    )
    assert renamed.json()["title"] == "Flange"
    assert (
        client.patch(
            f"/api/v1/conversations/{conv_id}", json={"title": "x"}, headers=b
        ).status_code
        == 404
    )

    searched = client.get("/api/v1/conversations", headers=a, params={"q": "Flange"})
    assert len(searched.json()["conversations"]) == 1

    assert client.delete(f"/api/v1/conversations/{conv_id}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/conversations/{conv_id}", headers=a).status_code == 204


def test_reopen_conversation_after_creating_new_chat(container: AppContainer) -> None:
    seed_grounded_chat(container)
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque?"}, headers=headers,
    )
    assert response.status_code == 200
    assert '"conversation_title": "What is torque?"' in response.text
    assert response.text.index("event: conversation") < response.text.index("event: sentence")
    assert '"title": "What is torque?"' in response.text
    new_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]

    listed = client.get("/api/v1/conversations", headers=headers).json()["conversations"]
    assert [c["id"] for c in listed] == [new_id, conv_id]
    assert listed[1]["title"] == "What is torque?"
    history = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "What is torque?"
    assert messages[1]["answer"]
    assert messages[1]["citations"]
    assert client.get(
        f"/api/v1/conversations/{new_id}/messages", headers=headers,
    ).json()["messages"] == []
    assert client.get(
        f"/api/v1/conversations/{conv_id}/messages", headers={"X-User-Id": "bob"},
    ).status_code == 404
    assert client.get(
        "/api/v1/conversations/missing/messages", headers=headers,
    ).status_code == 404


def test_default_title_uses_only_first_question_and_preserves_custom_titles() -> None:
    store = ConversationStore()
    for title in ["New chat", "Custom title"]:
        conv = store.create(user_id="alice", workspace_id="default", title=title)
        for content in ["  What\n is torque?  ", "How does it work?"]:
            store.add_message(conv.id, "alice", MessageRecord(
                id=store.new_message_id(), conversation_id=conv.id, role="user", content=content,
            ))
        assert conv.title == ("What is torque?" if title == "New chat" else title)


def test_message_stream_emits_a_real_retrieval_trace(container: AppContainer) -> None:
    """Backs the chat page's "why this answer" panel — must be real retrieval facts
    (the query actually searched, the collections actually scoped, how many sources
    came back, how long it took), not a placeholder string."""
    seed_grounded_chat(container)
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque?", "scope": {"collections": ["ops"]}},
        headers=headers,
    )
    assert response.status_code == 200
    block = next(b for b in response.text.split("\n\n") if "\nevent: trace\n" in b)
    data = json.loads(block.split("data: ", 1)[1])
    assert data["resolved_query"] == "What is torque?"
    assert data["route"] == "doc_qa"
    assert data["collection_ids"] == ["ops"]
    assert data["evidence_count"] >= 1
    assert data["latency_ms"] >= 0


def test_refusal_history_preserves_the_response(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    headers = {"X-User-Id": "alice"}
    conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
    client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is torque?"}, headers=headers,
    )
    history = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers).json()
    assert history["title"] == "What is torque?"
    assert history["messages"][1]["content"]
    assert history["messages"][1]["refusal_type"]


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("  What\n is SYNCKIT?  ", "What is SYNCKIT?"),
        (
            "What is the recommended procedure for preparing a field survey?",
            "What is the recommended procedure for...",
        ),
        ("x" * 60, "x" * 45 + "..."),
        ("", "New chat"),
    ],
)
def test_titles_are_short_and_readable(question: str, expected: str) -> None:
    assert title_from_question(question) == expected
    assert len(title_from_question(question)) <= 48
