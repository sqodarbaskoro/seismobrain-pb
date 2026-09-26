"""
File: job_queue.py
Description: JobQueue port (framework-free) for durable background work
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

from collections.abc import Callable, Mapping
from typing import Protocol

JobHandler = Callable[[dict[str, object]], None]


class JobQueue(Protocol):
    """Port for enqueueing and running background jobs."""

    def register(self, name: str, handler: JobHandler) -> None:
        """Register a handler for a job name."""

    def enqueue(self, name: str, payload: Mapping[str, object]) -> str:
        """Enqueue a job and return its id."""

    def run_pending(self, timeout_seconds: float = 5.0) -> None:
        """Process pending jobs until idle or timeout (test/driver helper)."""

    def get_status(self, job_id: str) -> str:
        """Return job status: pending, running, succeeded, failed, or missing."""

    def close(self) -> None:
        """Release resources."""
