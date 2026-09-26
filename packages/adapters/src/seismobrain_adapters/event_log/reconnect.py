"""
File: reconnect.py
Description: EventLog reconnect resolution with finalized-message fallback (FR-CHAT-02)
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

from dataclasses import dataclass, field
from typing import Literal, Protocol

from seismobrain_core.ports import EventLog, LogEvent


class FinalizedMessageStore(Protocol):
    """PostgreSQL (or Starter SQLite) authority for finalized assistant messages."""

    def get_finalized(self, stream_id: str) -> dict[str, object] | None: ...


@dataclass(frozen=True)
class ReconnectResult:
    kind: Literal["replay", "finalized", "interrupted"]
    events: list[LogEvent] = field(default_factory=list)
    message: dict[str, object] | None = None


def resolve_reconnect(
    event_log: EventLog,
    finalized: FinalizedMessageStore,
    *,
    stream_id: str,
    last_event_id: str | None,
) -> ReconnectResult:
    """
    Resolve an SSE reconnect.

    Prefer EventLog replay when the stream still has events after Last-Event-ID.
    Otherwise return the finalized message from the metadata store (PG authority).
    If neither exists, return interrupted.
    """
    missed = event_log.replay(stream_id, after_id=last_event_id)
    if missed:
        return ReconnectResult(kind="replay", events=missed)
    final = finalized.get_finalized(stream_id)
    if final is not None:
        return ReconnectResult(kind="finalized", message=dict(final))
    return ReconnectResult(kind="interrupted")
