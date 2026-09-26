"""Framework-free durable stage checkpoint and event interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class PipelineEvent:
    job_id: str
    stage: str
    status: str
    started_at: float
    ended_at: float | None = None
    duration_ms: float | None = None
    counts: dict[str, int] = field(default_factory=dict)
    error: str | None = None


class PipelineCheckpoints(Protocol):
    def completed(self, job_id: str) -> list[str]: ...
    def mark_completed(self, job_id: str, stage: str) -> None: ...
    def attempts(self, job_id: str, stage: str) -> int: ...
    def bump_attempt(self, job_id: str, stage: str) -> int: ...
    def reset_attempts(self, job_id: str, stage: str) -> None: ...
    def mark_dead_letter(self, job_id: str, stage: str) -> None: ...
    def clear_dead_letter(self, job_id: str) -> str | None: ...
