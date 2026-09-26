"""
File: jobs.py
Description: Ingestion job name and shared enqueue helper (API enqueues; workers execute)
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

from collections.abc import Mapping

from seismobrain_core.ports import JobQueue

INGEST_JOB_NAME = "ingest.document"


def enqueue_ingest_job(queue: JobQueue, payload: Mapping[str, object]) -> str:
    """Enqueue an ingest job. Callers MUST NOT run the pipeline in-process."""
    return queue.enqueue(INGEST_JOB_NAME, dict(payload))
