"""Real process separation and recovery through the Starter ingestion handler."""

import multiprocessing
from pathlib import Path

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import InMemorySearchIndex
from seismobrain_api.starter_ingest import register_starter_ingest


def run_worker(root: str) -> None:
    path = Path(root)
    queue = InProcessJobQueue(path / "jobs")
    queue.store.retry_delay = 0
    container = AppContainer(
        settings=Settings(jwt_secret="a" * 64, master_key="b" * 64),
        metadata_store=SqliteMetadataStore(path / "meta.db"),
        job_queue=queue,
        object_store=FilesystemObjectStore(path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        search_index=InMemorySearchIndex(db_path=path / "index.db"),
    )
    register_starter_ingest(container)
    queue.run_pending()


def test_separate_worker_failure_restore_retry_and_restart(tmp_path: Path) -> None:
    queue = InProcessJobQueue(tmp_path / "jobs")
    object_store = FilesystemObjectStore(tmp_path / "objects")
    job_id = queue.enqueue(
        "ingest.document",
        {
            "document_id": "d",
            "collection_id": "c",
            "filename": "guide.md",
            "object_key": "guide.md",
        },
    )
    ctx = multiprocessing.get_context("spawn")

    def run() -> None:
        worker = ctx.Process(target=run_worker, args=(str(tmp_path),))
        worker.start()
        worker.join(15)
        if worker.is_alive():
            worker.terminate()
            worker.join()
            raise AssertionError("Worker did not finish")
        assert worker.exitcode == 0

    run()
    assert queue.get_status(job_id) == "dead_letter"
    assert queue.get_job(job_id).stage == "PARSED"
    object_store.put("guide.md", b"# Torque\n\nTorque is 40 Nm.")
    queue.job_action(job_id, "retry", actor="admin")
    run()
    restarted = InProcessJobQueue(tmp_path / "jobs")
    assert restarted.get_status(job_id) == "succeeded"
    assert restarted.get_job(job_id).attempts == 4
    hits = InMemorySearchIndex(db_path=tmp_path / "index.db").query(text="torque")
    assert hits and "40 Nm" in hits[0].text
    assert len({h.metadata["chunk_id"] for h in hits}) == len(hits)
    assert set(restarted.get_job(job_id).checkpoints) == {"PARSED", "CHUNKED", "INDEXED"}


def run_interrupted_worker(root: str) -> None:
    import time

    from seismobrain_core.job_execution import ingestion_stage

    path = Path(root)
    queue = InProcessJobQueue(path / "jobs")
    queue.store.lease_seconds = 0.3

    def paused(payload: dict[str, object]) -> None:
        with ingestion_stage("PARSED"):
            (path / "worker-started").write_text("started")
            time.sleep(30)

    queue.register("ingest.document", paused)
    queue.run_pending()


def test_killed_worker_is_recovered_by_replacement_process(tmp_path: Path) -> None:
    import time

    queue = InProcessJobQueue(tmp_path / "jobs")
    FilesystemObjectStore(tmp_path / "objects").put("guide.md", b"# Guide\n\nTorque is 40 Nm.")
    job_id = queue.enqueue(
        "ingest.document",
        {
            "document_id": "d",
            "collection_id": "c",
            "filename": "guide.md",
            "object_key": "guide.md",
        },
    )
    ctx = multiprocessing.get_context("spawn")
    original = ctx.Process(target=run_interrupted_worker, args=(str(tmp_path),))
    original.start()
    try:
        deadline = time.monotonic() + 10
        while not (tmp_path / "worker-started").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert (tmp_path / "worker-started").exists()
        assert queue.get_status(job_id) == "running"
        assert queue.reclaim_interrupted() == 0
    finally:
        original.terminate()
        original.join(5)
    time.sleep(0.4)
    replacement = ctx.Process(target=run_worker, args=(str(tmp_path),))
    replacement.start()
    replacement.join(15)
    if replacement.is_alive():
        replacement.terminate()
        replacement.join()
        raise AssertionError("Replacement worker did not finish")
    assert replacement.exitcode == 0
    assert queue.get_status(job_id) == "succeeded"
    assert queue.get_job(job_id).attempts == 2
    assert any(event.status == "interrupted" for event in queue.get_job(job_id).events)
    hits = InMemorySearchIndex(db_path=tmp_path / "index.db").query(text="torque")
    assert len(hits) == 1
