"""
File: ingest_worker.py
Description: Durable ingest worker — reclaim interrupted jobs and execute handlers
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

from seismobrain_core.ports import JobHandler, JobQueue
from seismobrain_ingest.jobs import INGEST_JOB_NAME


class IngestWorker:
    """Runs ingest jobs from a durable JobQueue; reclaims interrupted work on start."""

    def __init__(self, queue: JobQueue, *, handler: JobHandler) -> None:
        self._queue = queue
        reclaim = getattr(queue, "reclaim_interrupted", None)
        if callable(reclaim):
            reclaim()
        queue.register(INGEST_JOB_NAME, handler)

    def run(self, timeout_seconds: float = 5.0) -> None:
        self._queue.run_pending(timeout_seconds=timeout_seconds)
