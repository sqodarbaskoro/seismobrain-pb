from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Thread

import pytest

from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_core.ingestion_jobs import JobConflict
from seismobrain_core.job_execution import ingestion_stage


def test_second_worker_does_not_reclaim_live_work(tmp_path: Path) -> None:
    first = InProcessJobQueue(tmp_path / "jobs")
    second = InProcessJobQueue(tmp_path / "jobs")
    entered, release = Event(), Event()

    def handler(payload: dict[str, object]) -> None:
        with ingestion_stage("PARSED"):
            entered.set()
            assert release.wait(5)

    first.register("ingest.document", handler)
    job_id = first.enqueue("ingest.document", {})
    thread = Thread(target=first.run_pending)
    thread.start()
    try:
        assert entered.wait(5)
        assert second.reclaim_interrupted() == 0
        assert second.store.claim(job_id) is None
    finally:
        release.set()
        thread.join(5)
    assert second.get_status(job_id) == "succeeded"


def test_quarantine_running_job_stops_before_publication(tmp_path: Path) -> None:
    queue = InProcessJobQueue(tmp_path / "jobs")
    entered, release = Event(), Event()
    published: list[bool] = []

    def handler(payload: dict[str, object]) -> None:
        with ingestion_stage("PARSED"):
            entered.set()
            assert release.wait(5)
        with ingestion_stage("INDEXED"):
            published.append(True)

    queue.register("ingest.document", handler)
    job_id = queue.enqueue("ingest.document", {})
    thread = Thread(target=queue.run_pending)
    thread.start()
    try:
        assert entered.wait(5)
        queue.job_action(job_id, "quarantine", actor="admin", reason="Inspect")
        with pytest.raises(JobConflict, match="stopping"):
            queue.job_action(job_id, "release", actor="admin")
    finally:
        release.set()
        thread.join(5)
    assert not published
    assert queue.get_status(job_id) == "quarantined"
    queue.job_action(job_id, "release", actor="admin")
    queue.run_pending()
    assert published == [True]


def test_concurrent_retry_only_one_succeeds(tmp_path: Path) -> None:
    first = InProcessJobQueue(tmp_path / "jobs")
    first.store.retry_delay = 0
    second = InProcessJobQueue(tmp_path / "jobs")
    job_id = first.enqueue("ingest.document", {})
    first.run_pending()

    def retry(queue: InProcessJobQueue) -> bool:
        try:
            queue.job_action(job_id, "retry", actor="admin")
            return True
        except JobConflict:
            return False

    with ThreadPoolExecutor(2) as pool:
        assert sum(pool.map(retry, [first, second])) == 1
    assert first.get_job(job_id).attempts == 3


def test_legacy_json_jobs_import_without_fabricated_history(tmp_path: Path) -> None:
    import json

    root = tmp_path / "jobs"
    root.mkdir()
    (root / "old.json").write_text(
        json.dumps(
            {
                "id": "old",
                "name": "ingest.document",
                "payload": {"filename": "old.md"},
                "status": "succeeded",
            }
        )
    )
    queue = InProcessJobQueue(root)
    assert queue.get_status("old") == "succeeded"
    assert queue.get_job("old").stage == "UNKNOWN"
    assert not queue.get_job("old").history_available
    assert not queue.get_job("old").events
    assert InProcessJobQueue(root).list_jobs().total == 1
