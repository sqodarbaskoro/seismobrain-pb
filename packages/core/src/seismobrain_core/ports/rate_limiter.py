"""
File: rate_limiter.py
Description: RateLimiter port (framework-free) for configurable request limits
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

from typing import Protocol


class RateLimiter(Protocol):
    """Port for fixed-window rate limiting with configurable limits."""

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        """Return True if the request is allowed under the limit for the window."""

    def close(self) -> None:
        """Release resources."""
