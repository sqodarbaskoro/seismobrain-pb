"""
File: in_memory.py
Description: In-memory RateLimiter for Starter tier (single process)
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

import threading
import time


class InMemoryRateLimiter:
    """Starter RateLimiter using an in-process fixed window counter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, int]] = {}

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if limit < 1 or window_seconds < 1:
            raise ValueError("limit and window_seconds must be >= 1")
        now = int(time.time())
        window_start = now - (now % window_seconds)
        bucket = f"{key}:{window_start}:{window_seconds}"
        with self._lock:
            count, start = self._windows.get(bucket, (0, window_start))
            if start != window_start:
                count = 0
            if count >= limit:
                return False
            self._windows[bucket] = (count + 1, window_start)
            return True

    def close(self) -> None:
        return
