from pathlib import Path

from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.queue.job_store import SqlJobStore
from seismobrain_adapters.queue.pipeline_state import SqlPipelineState
from seismobrain_ingest.pipeline import IngestionPipeline


def test_pipeline_checkpoints_resume_after_store_restart(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'jobs.db'}"
    store = SqlJobStore(url)
    job = store.enqueue("ingest.document", {})
    state = SqlPipelineState(store)

    def failing(stage: str, version: str) -> dict[str, int]:
        if stage == "CHUNKED":
            raise ValueError("Sensitive text")
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=InMemoryEventLog(),
        job_events=state,
        checkpoints=state,
        stage_runner=failing,
        base_backoff_seconds=0,
    )
    assert pipeline.run(job_id=job.id, version_id="v").status == "DEAD_LETTER"
    assert state.attempts(job.id, "CHUNKED") == 3
    restarted = SqlJobStore(url)
    restored = SqlPipelineState(restarted)
    assert "PARSED" in restored.completed(job.id)
    seen: list[str] = []

    def successful(stage: str, version: str) -> dict[str, int]:
        seen.append(stage)
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=InMemoryEventLog(),
        job_events=restored,
        checkpoints=restored,
        stage_runner=successful,
    )
    assert pipeline.manual_retry(job_id=job.id, version_id="v").status == "READY"
    assert seen[0] == "CHUNKED"
    assert "PARSED" not in seen
    assert "Sensitive text" not in restarted.get(job.id).model_dump_json()
