"""
File: rate_limit.py
Description: Helpers to enforce SEC-10 rate limits via RateLimiter port
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

from fastapi import HTTPException, Request

from seismobrain_api.container import AppContainer


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def enforce_limit(
    container: AppContainer, *, key: str, limit: int, window_seconds: int
) -> None:
    if not container.rate_limiter.allow(
        key, limit=limit, window_seconds=window_seconds
    ):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
