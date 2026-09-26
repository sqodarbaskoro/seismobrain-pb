"""
File: test_ingest_enqueue_durability.py
Description: FR-ING-01 — API enqueues ingest jobs; durable workers execute; kill does not lose job
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

from pathlib import Path

from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_api.ingest_enqueue import enqueue_ingest
from seismobrain_ingest.jobs import INGEST_JOB_NAME
from seismobrain_worker.ingest_worker import IngestWorker


def test_api_enqueues_only_worker_executes_and_survives_kill(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    marker = tmp_path / "ingested.txt"

    # API process: enqueue only — no ingest handler, never run_pending.
    api_queue = InProcessJobQueue(jobs_dir)
    job_id = enqueue_ingest(
        api_queue,
        document_id="doc-1",
        collection_id="col-1",
        marker_path=str(marker),
    )
    assert job_id
    assert api_queue.get_status(job_id) == "pending"
    assert not marker.exists()
    # API must not register the ingest handler.
    assert INGEST_JOB_NAME not in api_queue._handlers  # noqa: SLF001

    # Simulate a worker that claimed the job then died before finishing.
    api_queue.store.lease_seconds = -1
    assert api_queue.store.claim(job_id) is not None
    assert api_queue.get_status(job_id) == "running"
    assert not marker.exists()

    # Replacement worker reclaims interrupted jobs and executes ingestion.
    executed: list[str] = []

    def handler(payload: dict[str, object]) -> None:
        executed.append(str(payload["document_id"]))
        Path(str(payload["marker_path"])).write_text("ok", encoding="utf-8")

    worker = IngestWorker(InProcessJobQueue(jobs_dir), handler=handler)
    worker.run(timeout_seconds=5.0)

    assert executed == ["doc-1"]
    assert marker.read_text(encoding="utf-8") == "ok"
    assert InProcessJobQueue(jobs_dir).get_status(job_id) == "succeeded"
