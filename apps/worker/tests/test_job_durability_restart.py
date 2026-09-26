"""
File: test_job_durability_restart.py
Description: NFR-REL-02 — 100% of jobs resumed or retried after worker/host restart
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
from seismobrain_worker.ingest_worker import IngestWorker


def test_all_jobs_resume_after_worker_restart(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    api_queue = InProcessJobQueue(jobs_dir)
    job_ids = [
        enqueue_ingest(api_queue, document_id=f"doc-{i}", collection_id="col-1")
        for i in range(5)
    ]

    # Simulate host crash: two jobs stuck running, three still pending.
    api_queue.store.lease_seconds = -1
    for job_id in job_ids[:2]:
        assert api_queue.store.claim(job_id) is not None

    done: list[str] = []

    def handler(payload: dict[str, object]) -> None:
        done.append(str(payload["document_id"]))

    # Restarted worker reclaims interrupted jobs and drains the queue.
    worker = IngestWorker(InProcessJobQueue(jobs_dir), handler=handler)
    worker.run(timeout_seconds=5.0)

    assert sorted(done) == [f"doc-{i}" for i in range(5)]
    restarted = InProcessJobQueue(jobs_dir)
    assert all(restarted.get_status(job_id) == "succeeded" for job_id in job_ids)
