"""
File: in_memory.py
Description: In-memory ring-buffer EventLog for Starter tier
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

import itertools
from collections import deque
from typing import Any

from seismobrain_core.ports import LogEvent


class InMemoryEventLog:
    """Starter EventLog: per-stream in-memory ring buffer."""

    def __init__(self, capacity: int = 1024) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._streams: dict[str, deque[LogEvent]] = {}
        self._counter = itertools.count(1)

    def append(self, stream_id: str, payload: dict[str, Any]) -> str:
        event_id = str(next(self._counter))
        event = LogEvent(event_id=event_id, payload=dict(payload))
        buf = self._streams.setdefault(stream_id, deque(maxlen=self._capacity))
        buf.append(event)
        return event_id

    def replay(self, stream_id: str, after_id: str | None) -> list[LogEvent]:
        buf = self._streams.get(stream_id)
        if not buf:
            return []
        if after_id is None:
            return list(buf)
        out: list[LogEvent] = []
        seen = False
        for event in buf:
            if seen:
                out.append(event)
            elif event.event_id == after_id:
                seen = True
        return out

    def close(self) -> None:
        return
