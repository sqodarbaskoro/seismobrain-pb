"""
File: test_event_log.py
Description: EventLog port tests: in-memory ring buffer and Redis Streams
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

from collections.abc import Iterator

import pytest
from testcontainers.community.redis import RedisContainer

from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.event_log.redis_streams import RedisStreamsEventLog
from seismobrain_core.ports import EventLog

_REDIS_IMAGE = "redis:7.4.2-alpine"
_STREAM = "conv:1"


def _assert_event_log_replay(log: EventLog) -> None:
    id1 = log.append(_STREAM, {"type": "token", "text": "Hel"})
    id2 = log.append(_STREAM, {"type": "token", "text": "lo"})
    assert id1
    assert id2
    assert id1 != id2
    # SSE event IDs are the log IDs.
    all_events = log.replay(_STREAM, after_id=None)
    assert [e.event_id for e in all_events] == [id1, id2]
    assert all_events[0].payload["text"] == "Hel"
    missed = log.replay(_STREAM, after_id=id1)
    assert [e.event_id for e in missed] == [id2]


def test_in_memory_event_log() -> None:
    log: EventLog = InMemoryEventLog(capacity=8)
    _assert_event_log_replay(log)


def test_in_memory_ring_buffer_drops_oldest() -> None:
    log = InMemoryEventLog(capacity=2)
    a = log.append(_STREAM, {"n": 1})
    b = log.append(_STREAM, {"n": 2})
    c = log.append(_STREAM, {"n": 3})
    events = log.replay(_STREAM, after_id=None)
    assert [e.event_id for e in events] == [b, c]
    assert a not in {e.event_id for e in events}


@pytest.fixture(scope="module")
def redis_url() -> Iterator[str]:
    with RedisContainer(_REDIS_IMAGE) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        yield f"redis://{host}:{port}/0"


def test_redis_streams_event_log(redis_url: str) -> None:
    log: EventLog = RedisStreamsEventLog(redis_url)
    try:
        _assert_event_log_replay(log)
    finally:
        log.close()
