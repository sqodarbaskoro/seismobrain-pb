from pathlib import Path

from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_api.search_index import IndexedHit, InMemorySearchIndex
from seismobrain_core.job_execution import ingestion_stage


def test_real_stage_events_and_errors_persist(tmp_path: Path) -> None:
    queue = InProcessJobQueue(tmp_path / "jobs")
    queue.store.retry_delay = 0

    def handler(payload: dict[str, object]) -> None:
        with ingestion_stage("PARSED") as counts:
            counts["pages"] = 2
        with ingestion_stage("CHUNKED"):
            raise ValueError("secret source text must not be exposed")

    queue.register("ingest.document", handler)
    job_id = queue.enqueue("ingest.document", {"filename": "test.md"})
    queue.run_pending()
    job = InProcessJobQueue(tmp_path / "jobs").get_job(job_id)
    assert job.stage == "CHUNKED"
    assert job.status == "dead_letter"
    assert job.attempts == 3
    assert job.checkpoints["PARSED"] == {"pages": 2}
    assert "secret source" not in job.model_dump_json()
    assert any(e.stage == "PARSED" and e.status == "succeeded" for e in job.events)


def test_atomic_index_replacement_is_idempotent_and_visible_after_restart(tmp_path: Path) -> None:
    path = tmp_path / "index.db"
    index = InMemorySearchIndex(db_path=path)
    hit = IndexedHit(document_id="d", version_id="v", text="torque", collection_id="c", score=1)
    index.replace_document("d", [hit])
    index.replace_document("d", [hit])
    assert len(InMemorySearchIndex(db_path=path).query(text="torque")) == 1
    index.replace_document("d", [])
    assert not InMemorySearchIndex(db_path=path).query(text="torque")
