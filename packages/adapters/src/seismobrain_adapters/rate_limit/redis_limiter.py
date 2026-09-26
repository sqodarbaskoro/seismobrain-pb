"""
File: redis_limiter.py
Description: Redis RateLimiter adapter for Team/Production tiers
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

import time

import redis


class RedisRateLimiter:
    """Team RateLimiter using Redis fixed-window counters."""

    def __init__(self, redis_url: str) -> None:
        self._client: redis.Redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if limit < 1 or window_seconds < 1:
            raise ValueError("limit and window_seconds must be >= 1")
        now = int(time.time())
        window_start = now - (now % window_seconds)
        bucket = f"rl:{key}:{window_start}:{window_seconds}"
        count = int(self._client.incr(bucket))
        if count == 1:
            self._client.expire(bucket, window_seconds)
        return count <= limit

    def close(self) -> None:
        self._client.close()
