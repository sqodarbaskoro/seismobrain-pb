"""
File: ingest_enqueue.py
Description: API-side ingest enqueue — registers nothing; workers execute FR-ING-01
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

from seismobrain_core.ports import JobQueue
from seismobrain_ingest.jobs import enqueue_ingest_job


def enqueue_ingest(
    queue: JobQueue,
    *,
    document_id: str,
    collection_id: str,
    **extra: object,
) -> str:
    """Enqueue document ingestion. Does not register handlers or run jobs."""
    payload: dict[str, object] = {
        "document_id": document_id,
        "collection_id": collection_id,
        **extra,
    }
    return enqueue_ingest_job(queue, payload)
