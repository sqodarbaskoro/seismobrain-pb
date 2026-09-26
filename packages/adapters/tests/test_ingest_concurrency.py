"""
File: test_ingest_concurrency.py
Description: FR-ING-03 — global and per-collection ingest concurrency enforced by the queue
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
from pathlib import Path

from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_ingest.jobs import INGEST_JOB_NAME


def test_global_and_per_collection_limits_hold_across_replicas(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    release = threading.Event()
    active_lock = threading.Lock()
    active_global = 0
    active_by_collection: dict[str, int] = {}
    peak_global = 0
    peak_by_collection: dict[str, int] = {}
    completed: list[str] = []

    def handler(payload: dict[str, object]) -> None:
        nonlocal active_global, peak_global
        collection_id = str(payload["collection_id"])
        with active_lock:
            active_global += 1
            active_by_collection[collection_id] = active_by_collection.get(collection_id, 0) + 1
            peak_global = max(peak_global, active_global)
            peak_by_collection[collection_id] = max(
                peak_by_collection.get(collection_id, 0),
                active_by_collection[collection_id],
            )
        assert release.wait(timeout=5.0)
        with active_lock:
            active_global -= 1
            active_by_collection[collection_id] -= 1
            completed.append(collection_id)

    # Two replicas share durable job storage (queue-enforced, not process memory).
    replica_a = InProcessJobQueue(
        jobs_dir, global_limit=2, per_collection_limit=1
    )
    replica_b = InProcessJobQueue(
        jobs_dir, global_limit=2, per_collection_limit=1
    )
    replica_a.register(INGEST_JOB_NAME, handler)
    replica_b.register(INGEST_JOB_NAME, handler)

    for i in range(3):
        replica_a.enqueue(INGEST_JOB_NAME, {"collection_id": "col-a", "n": i})
    for i in range(2):
        replica_a.enqueue(INGEST_JOB_NAME, {"collection_id": "col-b", "n": i})

    threads = [
        threading.Thread(target=replica_a.run_pending, kwargs={"timeout_seconds": 8.0}),
        threading.Thread(target=replica_b.run_pending, kwargs={"timeout_seconds": 8.0}),
    ]
    for thread in threads:
        thread.start()

    # Allow claims to start under the limits.
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        with active_lock:
            if peak_global >= 2:
                break
        time.sleep(0.02)

    with active_lock:
        assert peak_global <= 2
        assert peak_by_collection.get("col-a", 0) <= 1
        assert peak_by_collection.get("col-b", 0) <= 1
        assert active_global <= 2

    release.set()
    for thread in threads:
        thread.join(timeout=10.0)

    assert sorted(completed) == ["col-a", "col-a", "col-a", "col-b", "col-b"]
    assert peak_global <= 2
    assert peak_by_collection.get("col-a", 0) <= 1
    assert peak_by_collection.get("col-b", 0) <= 1
