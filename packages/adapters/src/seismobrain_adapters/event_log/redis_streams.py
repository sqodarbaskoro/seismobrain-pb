"""
File: redis_streams.py
Description: Redis Streams EventLog adapter for Team/Production (stream ID = SSE event ID)
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

import json
from typing import Any, cast

import redis

from seismobrain_core.ports import LogEvent


class RedisStreamsEventLog:
    """Team EventLog backed by Redis Streams; Redis stream entry IDs are SSE event IDs."""

    def __init__(self, redis_url: str) -> None:
        self._client: redis.Redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def append(self, stream_id: str, payload: dict[str, Any]) -> str:
        entry_id = self._client.xadd(stream_id, {"payload": json.dumps(payload)})
        return str(entry_id)

    def replay(self, stream_id: str, after_id: str | None) -> list[LogEvent]:
        start = f"({after_id}" if after_id is not None else "-"
        rows = cast(
            list[tuple[str, dict[str, str]]],
            self._client.xrange(stream_id, min=start, max="+"),
        )
        events: list[LogEvent] = []
        for entry_id, fields in rows:
            raw = fields.get("payload", "{}")
            events.append(LogEvent(event_id=entry_id, payload=json.loads(raw)))
        return events

    def close(self) -> None:
        self._client.close()
