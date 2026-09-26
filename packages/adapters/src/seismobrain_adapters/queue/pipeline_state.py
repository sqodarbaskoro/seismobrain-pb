"""SQL implementations of the reusable ingestion pipeline's state interfaces."""

from __future__ import annotations

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from seismobrain_adapters.queue.job_store import SqlJobStore, checkpoints
from seismobrain_core.ingestion_jobs import JobEvent
from seismobrain_core.pipeline_state import PipelineEvent


class SqlPipelineState:
    """Checkpoint store and event sink for an existing durable ingestion job.

    Pass this as both `checkpoints` and `job_events` to IngestionPipeline. The
    pipeline owns stage retries; its enclosing queue handler must not multiply
    retries when the pipeline returns a terminal DEAD_LETTER result.
    """

    def __init__(self, store: SqlJobStore):
        self.store = store

    def _ensure(self, conn: Connection, job_id: str, stage: str) -> None:
        if (
            conn.execute(
                select(checkpoints.c.job_id).where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
            ).first()
            is None
        ):
            conn.execute(insert(checkpoints).values(job_id=job_id, stage=stage))

    def completed(self, job_id: str) -> list[str]:
        with self.store.engine.connect() as conn:
            return list(
                conn.execute(
                    select(checkpoints.c.stage).where(
                        checkpoints.c.job_id == job_id,
                        checkpoints.c.completed == 1,
                    )
                ).scalars()
            )

    def mark_completed(self, job_id: str, stage: str) -> None:
        with self.store.transaction() as conn:
            self._ensure(conn, job_id, stage)
            conn.execute(
                update(checkpoints)
                .where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
                .values(completed=1)
            )

    def attempts(self, job_id: str, stage: str) -> int:
        with self.store.engine.connect() as conn:
            value = conn.execute(
                select(checkpoints.c.attempts).where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
            ).scalar_one_or_none()
            return int(value or 0)

    def bump_attempt(self, job_id: str, stage: str) -> int:
        with self.store.transaction() as conn:
            self._ensure(conn, job_id, stage)
            result = conn.execute(
                update(checkpoints)
                .where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
                .values(attempts=checkpoints.c.attempts + 1)
                .returning(checkpoints.c.attempts)
            )
            return int(result.scalar_one())

    def reset_attempts(self, job_id: str, stage: str) -> None:
        with self.store.transaction() as conn:
            self._ensure(conn, job_id, stage)
            conn.execute(
                update(checkpoints)
                .where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
                .values(attempts=0)
            )

    def mark_dead_letter(self, job_id: str, stage: str) -> None:
        with self.store.transaction() as conn:
            self._ensure(conn, job_id, stage)
            conn.execute(
                update(checkpoints)
                .where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.stage == stage,
                )
                .values(dead_letter=1)
            )

    def clear_dead_letter(self, job_id: str) -> str | None:
        with self.store.transaction() as conn:
            stage = conn.execute(
                select(checkpoints.c.stage).where(
                    checkpoints.c.job_id == job_id,
                    checkpoints.c.dead_letter == 1,
                )
            ).scalar_one_or_none()
            conn.execute(
                update(checkpoints)
                .where(checkpoints.c.job_id == job_id)
                .values(
                    dead_letter=0,
                )
            )
            return str(stage) if stage is not None else None

    def record(self, event: PipelineEvent) -> None:
        with self.store.transaction() as conn:
            job = self.store._get(conn, event.job_id)
            job.stage = event.stage
            # Do not persist raw exception text supplied by third-party stage runners.
            job.events.append(
                JobEvent(
                    stage=event.stage,
                    status=event.status,
                    timestamp=event.ended_at or event.started_at,
                    duration_ms=event.duration_ms,
                    counts=event.counts,
                    error=f"{event.stage} failed" if event.error else None,
                    attempt=self.attempts(event.job_id, event.stage),
                )
            )
            self.store._save(conn, job)
