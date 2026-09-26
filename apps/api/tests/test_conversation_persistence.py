"""
File: test_conversation_persistence.py
Description: Starter chat history, citations, and ownership survive server recreation
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.2.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from chat_fixtures import seed_grounded_chat
from fastapi.testclient import TestClient

from seismobrain_api.conversations import MessageRecord
from seismobrain_api.sqlite_conversations import SqliteConversationStore
from seismobrain_api.starter import build_starter_app


@pytest.fixture
def starter_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setattr("seismobrain_api.starter.start_ingest_worker", lambda _: None)
    (tmp_path / "spa").mkdir()
    (tmp_path / "spa" / "index.html").write_text("<html>Test</html>")
    return tmp_path


def test_starter_chat_survives_restart(starter_dir: Path) -> None:
    before = build_starter_app(starter_dir, starter_dir / "spa")
    seed_grounded_chat(before.state.container)
    headers = {"X-User-Id": "alice"}
    with TestClient(before) as client:
        conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
        stream = client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "What is torque?"}, headers=headers,
        )
        assert '"conversation_title": "What is torque?"' in stream.text
        saved = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers).json()
        assert len(saved["messages"]) == 2
        assert saved["messages"][1]["citations"]
        empty_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
    record = before.state.container.conversations.require_owner(conv_id, "alice")
    snapshots = record.messages[-1].evidence_snapshot_uris
    assert snapshots
    evidence = {
        uri: before.state.container.evidence_snapshots.get(uri) for uri in snapshots.values()
    }

    after = build_starter_app(starter_dir, starter_dir / "spa")
    after.state.container.llm_transport = before.state.container.llm_transport
    with TestClient(after) as client:
        assert "get" in client.get("/openapi.json").json()["paths"][
            "/api/v1/conversations/{conversation_id}/messages"
        ]
        restored = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
        assert restored.status_code == 200
        assert restored.json() == saved
        listed = client.get("/api/v1/conversations", headers=headers).json()["conversations"]
        assert [c["id"] for c in listed] == [empty_id, conv_id]
        assert client.get(
            f"/api/v1/conversations/{empty_id}/messages", headers=headers,
        ).json()["messages"] == []
        assert client.get(
            f"/api/v1/conversations/{conv_id}/messages", headers={"X-User-Id": "bob"},
        ).status_code == 404
        for uri, text in evidence.items():
            assert after.state.container.evidence_snapshots.get(uri) == text
        assistant_id = saved["messages"][-1]["id"]
        assert "Ops Manual" in client.get(
            f"/api/v1/conversations/{conv_id}/messages/{assistant_id}/copy", headers=headers,
        ).json()["markdown"]
        client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "How much is it?"}, headers=headers,
        )
        history = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers).json()
        assert len(history["messages"]) == 4
        assert history["messages"][:2] == saved["messages"]
        assert history["title"] == "What is torque?"


def test_question_survives_generation_failure(starter_dir: Path) -> None:
    app = build_starter_app(starter_dir, starter_dir / "spa")
    headers = {"X-User-Id": "alice"}
    with TestClient(app, raise_server_exceptions=False) as client:
        conv_id = client.post("/api/v1/conversations", json={}, headers=headers).json()["id"]
        with patch(
            "seismobrain_api.routes.conversations.run_conversation_doc_qa",
            side_effect=RuntimeError("generation failed"),
        ):
            client.post(
                f"/api/v1/conversations/{conv_id}/messages",
                json={"content": "Keep this question"}, headers=headers,
            )
    store = SqliteConversationStore(starter_dir / "conversations.db")
    record = store.require_owner(conv_id, "alice")
    assert [m.content for m in record.messages] == ["Keep this question"]
    assert record.title == "Keep this question"


def test_mutations_and_ownership_survive_reopening(tmp_path: Path) -> None:
    path = tmp_path / "conversations.db"
    store = SqliteConversationStore(path)
    record = store.create(user_id="alice", workspace_id="default")
    store.add_message(record.id, "alice", MessageRecord(
        id="answer", conversation_id=record.id, role="assistant", content="Saved answer",
    ))
    for mutation in [
        lambda: store.rename(record.id, "bob", "Wrong owner"),
        lambda: store.delete(record.id, "bob"),
        lambda: store.set_message_status(record.id, "answer", "bob", "interrupted"),
    ]:
        with pytest.raises(PermissionError):
            mutation()
    store.rename(record.id, "alice", "Custom name")
    store.set_message_status(record.id, "answer", "alice", "interrupted")
    reopened = SqliteConversationStore(path)
    restored = reopened.require_owner(record.id, "alice")
    assert restored.title == "Custom name"
    assert restored.messages[0].status == "interrupted"
    assert reopened.search("bob") == []
    assert reopened.search("alice", q="custom")[0].id == record.id
    reopened.delete(record.id, "alice")
    assert SqliteConversationStore(path).search("alice") == []


def test_concurrent_appends_do_not_lose_messages(tmp_path: Path) -> None:
    path = tmp_path / "conversations.db"
    store = SqliteConversationStore(path)
    record = store.create(user_id="alice", workspace_id="default")
    other = SqliteConversationStore(path)

    def append(index: int) -> None:
        target = store if index % 2 else other
        target.add_message(record.id, "alice", MessageRecord(
            id=f"msg_{index}", conversation_id=record.id, role="user", content=f"Question {index}",
        ))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(append, range(20)))
    restored = SqliteConversationStore(path).require_owner(record.id, "alice")
    assert {m.id for m in restored.messages} == {f"msg_{i}" for i in range(20)}


def test_old_placeholder_titles_are_repaired_without_changing_custom_names(tmp_path: Path) -> None:
    path = tmp_path / "conversations.db"
    store = SqliteConversationStore(path)
    ids = []
    for title in ["New chat", "My custom name"]:
        record = store.create(user_id="alice", workspace_id="default")
        store.add_message(record.id, "alice", MessageRecord(
            id=store.new_message_id(), conversation_id=record.id,
            role="user", content="What is SYNCKIT?",
        ))
        # Reproduce titles saved by the old server before automatic naming.
        store.rename(record.id, "alice", title)
        ids.append(record.id)
    reopened = SqliteConversationStore(path)
    assert reopened.require_owner(ids[0], "alice").title == "What is SYNCKIT?"
    assert reopened.require_owner(ids[1], "alice").title == "My custom name"
