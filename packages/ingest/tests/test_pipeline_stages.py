"""
File: test_pipeline_stages.py
Description: FR-ING-02 — stage-based ingest pipeline with job_events and EventLog progress
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
from seismobrain_ingest.pipeline import INGEST_STAGES, IngestionPipeline, JobEventRecorder


def test_pipeline_runs_stages_with_job_events_and_live_progress() -> None:
    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()
    pipeline = IngestionPipeline(event_log=event_log, job_events=recorder)

    result = pipeline.run(job_id="job-42", version_id="ver-1")

    assert result.status == "READY"
    assert result.stage == "READY"

    succeeded = [e for e in recorder.events if e.status == "succeeded"]
    assert [e.stage for e in succeeded] == list(INGEST_STAGES)
    for event in succeeded:
        assert event.started_at is not None
        assert event.ended_at is not None
        assert event.duration_ms is not None
        assert event.duration_ms >= 0
        assert isinstance(event.counts, dict)
        assert event.error is None

    stream = event_log.replay("job:job-42", after_id=None)
    assert stream, "expected live progress events on the job EventLog stream"
    payloads = [e.payload for e in stream]
    assert any(p.get("type") == "stage_progress" for p in payloads)
    progress_stages = [
        p["stage"]
        for p in payloads
        if p.get("type") == "stage_progress" and p.get("status") == "succeeded"
    ]
    assert progress_stages == list(INGEST_STAGES)
    assert any(p.get("status") == "started" for p in payloads if p.get("type") == "stage_progress")
