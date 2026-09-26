"""
File: event_log.py
Description: EventLog port (framework-free) for replayable SSE/job events
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

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class LogEvent:
    event_id: str
    payload: dict[str, Any]


class EventLog(Protocol):
    """Replayable event log; event_id is the SSE Last-Event-ID."""

    def append(self, stream_id: str, payload: dict[str, Any]) -> str:
        """Append an event and return its event id."""

    def replay(self, stream_id: str, after_id: str | None) -> list[LogEvent]:
        """Replay events after after_id (exclusive); None replays from the start."""

    def close(self) -> None:
        """Release resources."""
