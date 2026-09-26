from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from seismobrain_adapters.queue.job_store import SqlJobStore
from seismobrain_core.ingestion_jobs import JobConflict


def test_store_survives_restart_and_serializes_claims(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'jobs.db'}"
    first = SqlJobStore(url)
    job = first.enqueue("ingest.document", {"filename": "guide.md", "collection_id": "c"})
    second = SqlJobStore(url)
    with ThreadPoolExecutor(2) as pool:
        claims = list(pool.map(lambda store: store.claim(job.id), [first, second]))
    assert sum(claim is not None for claim in claims) == 1
    assert second.get(job.id).status == "running"
    assert second.summary().running == 1
    assert second.summary().queue_depth == 0


def test_retry_is_real_and_preserves_history(tmp_path: Path) -> None:
    store = SqlJobStore(f"sqlite:///{tmp_path / 'jobs.db'}", retry_delay=0)
    job = store.enqueue("ingest.document", {"filename": "guide.md"})
    for _ in range(3):
        claim = store.claim(job.id)
        assert claim is not None
        store.finish(job.id, claim.owner, error="Parsing failed")
    assert store.get(job.id).status == "dead_letter"
    store.action(job.id, "retry", actor="admin")
    with pytest.raises(JobConflict):
        store.action(job.id, "retry", actor="admin")
    reopened = SqlJobStore(f"sqlite:///{tmp_path / 'jobs.db'}")
    assert reopened.get(job.id).status == "pending"
    assert reopened.get(job.id).attempts == 3
    assert len(reopened.get(job.id).events) >= 7


def test_quarantine_blocks_claim_and_release_requeues(tmp_path: Path) -> None:
    store = SqlJobStore(f"sqlite:///{tmp_path / 'jobs.db'}")
    job = store.enqueue("ingest.document", {})
    store.action(job.id, "quarantine", actor="admin", reason="Check source")
    assert store.claim(job.id) is None
    with pytest.raises(JobConflict):
        store.action(job.id, "retry", actor="admin")
    store.action(job.id, "release", actor="admin")
    assert store.claim(job.id) is not None


def test_expired_worker_cannot_overwrite_new_owner(tmp_path: Path) -> None:
    store = SqlJobStore(f"sqlite:///{tmp_path / 'jobs.db'}", lease_seconds=-1)
    job = store.enqueue("ingest.document", {})
    old = store.claim(job.id)
    assert old is not None
    assert store.reclaim() == 1
    store.lease_seconds = 30
    current = store.claim(job.id)
    assert current is not None
    store.finish(job.id, old.owner)
    assert store.get(job.id).status == "running"
    store.finish(job.id, current.owner)
    assert store.get(job.id).status == "succeeded"


def test_expired_worker_cannot_complete_or_renew_lease(tmp_path: Path) -> None:
    store = SqlJobStore(f"sqlite:///{tmp_path / 'jobs.db'}", lease_seconds=-1)
    job = store.enqueue("ingest.document", {})
    old = store.claim(job.id)
    assert old is not None
    store.lease_seconds = 30
    store.heartbeat(job.id, old.owner)
    store.finish(job.id, old.owner)
    assert store.get(job.id).status == "pending"
    assert "lease expired" in (store.get(job.id).error or "")
