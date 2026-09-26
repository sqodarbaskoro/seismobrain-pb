"""
File: health.py
Description: Shared health and readiness response contracts
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

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness payload for GET /health."""

    status: str = Field(min_length=1)


class ReadyResponse(BaseModel):
    """Readiness payload for GET /ready."""

    status: str = Field(min_length=1)
    checks: dict[str, bool]
