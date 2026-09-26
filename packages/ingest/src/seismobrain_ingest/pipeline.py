"""
File: pipeline.py
Description: Stage-based ingestion pipeline with job_events, checkpoints, and retries
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from seismobrain_core.pipeline_state import PipelineCheckpoints
from seismobrain_core.pipeline_state import PipelineEvent as JobEvent
from seismobrain_core.ports import EventLog

# PRD §8.1 ingestion state machine (happy path).
INGEST_STAGES: tuple[str, ...] = (
    "RECEIVED",
    "STORED",
    "SCANNED",
    "CONVERTED",
    "PARSED",
    "ENRICHED",
    "CHUNKED",
    "EMBEDDED",
    "INDEXED",
    "VERIFIED",
    "READY",
)

StageRunner = Callable[[str, str], dict[str, int]]


@dataclass(slots=True)
class PipelineResult:
    job_id: str
    stage: str
    status: str
    error: str | None = None


class JobEventSink(Protocol):
    def record(self, event: JobEvent) -> None: ...


class JobEventRecorder:
    """In-memory job_events sink (metadata store wiring comes later)."""

    def __init__(self) -> None:
        self.events: list[JobEvent] = []

    def record(self, event: JobEvent) -> None:
        self.events.append(event)


class StageCheckpointStore:
    """Idempotent per-job stage checkpoints and attempt counters."""

    def __init__(self) -> None:
        self._completed: dict[str, list[str]] = {}
        self._attempts: dict[tuple[str, str], int] = {}
        self._dead_letter_stage: dict[str, str] = {}

    def completed(self, job_id: str) -> list[str]:
        return list(self._completed.get(job_id, []))

    def mark_completed(self, job_id: str, stage: str) -> None:
        done = self._completed.setdefault(job_id, [])
        if stage not in done:
            done.append(stage)

    def attempts(self, job_id: str, stage: str) -> int:
        return self._attempts.get((job_id, stage), 0)

    def bump_attempt(self, job_id: str, stage: str) -> int:
        key = (job_id, stage)
        self._attempts[key] = self._attempts.get(key, 0) + 1
        return self._attempts[key]

    def reset_attempts(self, job_id: str, stage: str) -> None:
        self._attempts[(job_id, stage)] = 0

    def mark_dead_letter(self, job_id: str, stage: str) -> None:
        self._dead_letter_stage[job_id] = stage

    def clear_dead_letter(self, job_id: str) -> str | None:
        return self._dead_letter_stage.pop(job_id, None)


def _default_stage_runner(stage: str, version_id: str) -> dict[str, int]:
    _ = version_id
    return {"items": 1 if stage not in {"RECEIVED", "READY"} else 0}


class IngestionPipeline:
    """Runs §8.1 stages with checkpoints, retries, and EventLog progress."""

    def __init__(
        self,
        *,
        event_log: EventLog,
        job_events: JobEventSink,
        checkpoints: PipelineCheckpoints | None = None,
        stage_runner: StageRunner | None = None,
        max_attempts: int = 3,
        base_backoff_seconds: float = 1.0,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._event_log = event_log
        self._job_events = job_events
        self._checkpoints = checkpoints or StageCheckpointStore()
        self._stage_runner = stage_runner or _default_stage_runner
        self._max_attempts = max_attempts
        self._base_backoff_seconds = base_backoff_seconds

    def run(self, *, job_id: str, version_id: str) -> PipelineResult:
        stream_id = f"job:{job_id}"
        for stage in INGEST_STAGES:
            if stage in self._checkpoints.completed(job_id):
                continue
            while True:
                attempt = self._checkpoints.bump_attempt(job_id, stage)
                started = time.perf_counter()
                started_at = time.time()
                self._job_events.record(
                    JobEvent(
                        job_id=job_id,
                        stage=stage,
                        status="started",
                        started_at=started_at,
                    )
                )
                self._event_log.append(
                    stream_id,
                    {
                        "type": "stage_progress",
                        "job_id": job_id,
                        "version_id": version_id,
                        "stage": stage,
                        "status": "started",
                        "attempt": attempt,
                    },
                )
                try:
                    counts = self._stage_runner(stage, version_id)
                except Exception as exc:
                    error = str(exc)
                    ended_at = time.time()
                    duration_ms = (time.perf_counter() - started) * 1000.0
                    self._job_events.record(
                        JobEvent(
                            job_id=job_id,
                            stage=stage,
                            status="failed",
                            started_at=started_at,
                            ended_at=ended_at,
                            duration_ms=duration_ms,
                            error=error,
                        )
                    )
                    self._event_log.append(
                        stream_id,
                        {
                            "type": "stage_progress",
                            "job_id": job_id,
                            "version_id": version_id,
                            "stage": stage,
                            "status": "failed",
                            "attempt": attempt,
                            "error": error,
                        },
                    )
                    if attempt >= self._max_attempts:
                        self._checkpoints.mark_dead_letter(job_id, stage)
                        self._event_log.append(
                            stream_id,
                            {
                                "type": "dead_letter",
                                "job_id": job_id,
                                "stage": stage,
                                "error": error,
                                "attempts": attempt,
                            },
                        )
                        return PipelineResult(
                            job_id=job_id,
                            stage=stage,
                            status="DEAD_LETTER",
                            error=error,
                        )
                    time.sleep(self._base_backoff_seconds * (2 ** (attempt - 1)))
                    continue

                ended_at = time.time()
                duration_ms = (time.perf_counter() - started) * 1000.0
                self._checkpoints.mark_completed(job_id, stage)
                self._job_events.record(
                    JobEvent(
                        job_id=job_id,
                        stage=stage,
                        status="succeeded",
                        started_at=started_at,
                        ended_at=ended_at,
                        duration_ms=duration_ms,
                        counts=counts,
                    )
                )
                self._event_log.append(
                    stream_id,
                    {
                        "type": "stage_progress",
                        "job_id": job_id,
                        "version_id": version_id,
                        "stage": stage,
                        "status": "succeeded",
                        "duration_ms": duration_ms,
                        "counts": counts,
                        "attempt": attempt,
                    },
                )
                break
        return PipelineResult(job_id=job_id, stage="READY", status="READY")

    def manual_retry(self, *, job_id: str, version_id: str) -> PipelineResult:
        """Clear dead-letter and resume from the failed stage (FR-ING-05)."""
        stage = self._checkpoints.clear_dead_letter(job_id)
        if stage is not None:
            self._checkpoints.reset_attempts(job_id, stage)
        return self.run(job_id=job_id, version_id=version_id)
