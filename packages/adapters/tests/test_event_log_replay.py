"""
File: test_event_log_replay.py
Description: SSE Last-Event-ID reconnect replay contract (FR-CHAT-02 / T0c.4)
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

from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.event_log.reconnect import (
    FinalizedMessageStore,
    ReconnectResult,
    resolve_reconnect,
)


class _FinalStore:
    def __init__(self) -> None:
        self._final: dict[str, dict[str, object]] = {}

    def get_finalized(self, stream_id: str) -> dict[str, object] | None:
        return self._final.get(stream_id)

    def set_finalized(self, stream_id: str, message: dict[str, object]) -> None:
        self._final[stream_id] = message


def test_reconnect_replays_missed_events_from_log() -> None:
    log = InMemoryEventLog()
    store: FinalizedMessageStore = _FinalStore()
    first = log.append("msg-1", {"type": "token", "text": "A"})
    second = log.append("msg-1", {"type": "token", "text": "B"})
    result = resolve_reconnect(
        log, store, stream_id="msg-1", last_event_id=first
    )
    assert result.kind == "replay"
    assert [e.event_id for e in result.events] == [second]
    assert result.events[0].event_id == second  # SSE IDs are log IDs


def test_expired_stream_returns_finalized_message_from_postgres_authority() -> None:
    log = InMemoryEventLog()
    store = _FinalStore()
    store.set_finalized(
        "msg-2",
        {"id": "msg-2", "text": "final answer", "status": "finalized"},
    )
    result = resolve_reconnect(
        log, store, stream_id="msg-2", last_event_id="stale-id"
    )
    assert result.kind == "finalized"
    assert result.message is not None
    assert result.message["status"] == "finalized"


def test_missing_stream_and_final_returns_interrupted() -> None:
    log = InMemoryEventLog()
    store = _FinalStore()
    result = resolve_reconnect(
        log, store, stream_id="msg-3", last_event_id=None
    )
    assert result == ReconnectResult(kind="interrupted", events=[], message=None)
