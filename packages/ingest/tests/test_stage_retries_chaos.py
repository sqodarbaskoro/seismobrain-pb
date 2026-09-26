"""
File: test_stage_retries_chaos.py
Description: FR-ING-05 — checkpointed stages, exponential backoff retries, dead-letter, manual retry
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

from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_ingest.pipeline import (
    INGEST_STAGES,
    IngestionPipeline,
    JobEventRecorder,
    StageCheckpointStore,
)


def test_chaos_retries_with_backoff_then_reaches_ready(monkeypatch: object) -> None:
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("seismobrain_ingest.pipeline.time.sleep", fake_sleep)  # type: ignore[attr-defined]

    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()
    checkpoints = StageCheckpointStore()
    failures_left = {"PARSED": 2}

    def flaky(stage: str, version_id: str) -> dict[str, int]:
        _ = version_id
        if failures_left.get(stage, 0) > 0:
            failures_left[stage] -= 1
            raise RuntimeError(f"chaos:{stage}")
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=event_log,
        job_events=recorder,
        checkpoints=checkpoints,
        stage_runner=flaky,
        max_attempts=3,
    )
    result = pipeline.run(job_id="job-chaos", version_id="ver-1")
    assert result.status == "READY"
    assert failures_left["PARSED"] == 0
    assert sleeps == [1.0, 2.0]
    assert checkpoints.completed("job-chaos") == list(INGEST_STAGES)


def test_dead_letter_after_max_retries_and_manual_retry(monkeypatch: object) -> None:
    monkeypatch.setattr("seismobrain_ingest.pipeline.time.sleep", lambda _s: None)  # type: ignore[attr-defined]

    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()
    checkpoints = StageCheckpointStore()

    def always_fail_parsed(stage: str, version_id: str) -> dict[str, int]:
        _ = version_id
        if stage == "PARSED":
            raise RuntimeError("permanent parse failure")
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=event_log,
        job_events=recorder,
        checkpoints=checkpoints,
        stage_runner=always_fail_parsed,
        max_attempts=3,
    )
    result = pipeline.run(job_id="job-dead", version_id="ver-1")
    assert result.status == "DEAD_LETTER"
    assert result.stage == "PARSED"
    assert result.error is not None
    assert "permanent parse failure" in result.error
    assert checkpoints.attempts("job-dead", "PARSED") == 3
    assert "CONVERTED" in checkpoints.completed("job-dead")
    assert "PARSED" not in checkpoints.completed("job-dead")

    successes: dict[str, int] = {"PARSED": 0}

    def recover(stage: str, version_id: str) -> dict[str, int]:
        _ = version_id
        if stage == "PARSED":
            successes["PARSED"] += 1
        return {"items": 1}

    pipeline_recovered = IngestionPipeline(
        event_log=event_log,
        job_events=recorder,
        checkpoints=checkpoints,
        stage_runner=recover,
        max_attempts=3,
    )
    retried = pipeline_recovered.manual_retry(job_id="job-dead", version_id="ver-1")
    assert retried.status == "READY"
    assert successes["PARSED"] == 1
    assert checkpoints.completed("job-dead") == list(INGEST_STAGES)


def test_checkpointed_stages_are_not_re_executed(monkeypatch: object) -> None:
    monkeypatch.setattr("seismobrain_ingest.pipeline.time.sleep", lambda _s: None)  # type: ignore[attr-defined]

    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()
    checkpoints = StageCheckpointStore()
    run_counts: dict[str, int] = {}

    def counting(stage: str, version_id: str) -> dict[str, int]:
        _ = version_id
        run_counts[stage] = run_counts.get(stage, 0) + 1
        if stage == "CHUNKED" and run_counts[stage] == 1:
            raise RuntimeError("kill after chunk")
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=event_log,
        job_events=recorder,
        checkpoints=checkpoints,
        stage_runner=counting,
        max_attempts=3,
    )
    first = pipeline.run(job_id="job-ckpt", version_id="ver-1")
    assert first.status == "READY"
    assert run_counts["STORED"] == 1
    assert run_counts["CHUNKED"] == 2
    assert run_counts["EMBEDDED"] == 1
