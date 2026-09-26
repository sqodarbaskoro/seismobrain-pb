"""
File: test_rate_limiter.py
Description: RateLimiter port tests: in-memory Starter and Redis Team
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

from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_adapters.rate_limit.redis_limiter import RedisRateLimiter
from seismobrain_core.ports import RateLimiter

_REDIS_IMAGE = "redis:7.4.2-alpine"


def _assert_limiter(limiter: RateLimiter) -> None:
    key = "auth:ip:1.2.3.4"
    assert limiter.allow(key, limit=2, window_seconds=60) is True
    assert limiter.allow(key, limit=2, window_seconds=60) is True
    assert limiter.allow(key, limit=2, window_seconds=60) is False


def test_in_memory_rate_limiter() -> None:
    limiter: RateLimiter = InMemoryRateLimiter()
    _assert_limiter(limiter)


@pytest.fixture(scope="module")
def redis_url() -> Iterator[str]:
    with RedisContainer(_REDIS_IMAGE) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        yield f"redis://{host}:{port}/0"


def test_redis_rate_limiter(redis_url: str) -> None:
    limiter: RateLimiter = RedisRateLimiter(redis_url)
    try:
        _assert_limiter(limiter)
    finally:
        limiter.close()
