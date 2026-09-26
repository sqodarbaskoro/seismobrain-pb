"""Shared ingestion lifecycle, public monitoring records, and monitoring port."""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

JobStatus = Literal["pending", "running", "succeeded", "failed", "dead_letter", "quarantined"]
JobAction = Literal["retry", "quarantine", "release"]
INGEST_JOB = "ingest.document"


class JobConflict(Exception):
    """The requested action is incompatible with the current job state."""


class JobStopped(Exception):
    """The worker lost ownership or the job was quarantined."""


class JobEvent(BaseModel):
    stage: str
    status: str
    timestamp: float
    attempt: int = 0
    duration_ms: float | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    error: str | None = None
    actor: str | None = None
    reason: str | None = None


class IngestionJob(BaseModel):
    id: str
    name: str = INGEST_JOB
    document_id: str = ""
    collection_id: str = ""
    version_id: str = ""
    filename: str = ""
    status: JobStatus = "pending"
    stage: str = "QUEUED"
    attempts: int = 0
    cycle_attempts: int = 0
    created_at: float
    updated_at: float
    started_at: float | None = None
    ended_at: float | None = None
    next_attempt_at: float = 0
    error: str | None = None
    quarantine_reason: str | None = None
    history_available: bool = True
    events: list[JobEvent] = Field(default_factory=list)
    checkpoints: dict[str, dict[str, int]] = Field(default_factory=dict)
    actions: list[JobAction] = Field(default_factory=list)


class JobPage(BaseModel):
    jobs: list[IngestionJob]
    total: int
    offset: int
    limit: int


class IngestionSummary(BaseModel):
    queue_depth: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    dead_letter: int = 0
    quarantined: int = 0
    stages: dict[str, int] = Field(default_factory=dict)
    updated_at: float
    scope: str = "All retained ingestion jobs; stage counts include running jobs only."


def allowed_actions(status: JobStatus) -> list[JobAction]:
    if status == "quarantined":
        return ["release"]
    if status in {"failed", "dead_letter"}:
        return ["retry", "quarantine"]
    if status in {"pending", "running"}:
        return ["quarantine"]
    return []


@runtime_checkable
class IngestionMonitor(Protocol):
    def summary(self) -> IngestionSummary: ...
    def list_jobs(
        self,
        *,
        status: JobStatus | None = None,
        collection_id: str = "",
        search: str = "",
        offset: int = 0,
        limit: int = 25,
    ) -> JobPage: ...
    def get_job(self, job_id: str) -> IngestionJob: ...
    def job_action(
        self,
        job_id: str,
        action: JobAction,
        *,
        actor: str,
        reason: str = "",
    ) -> IngestionJob: ...
