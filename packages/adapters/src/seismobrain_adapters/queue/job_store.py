"""Durable queue state shared by SQLite and PostgreSQL, including a dispatch outbox.

A database mutex serializes short mutations (never document processing). This also
makes collection concurrency limits and administrator actions atomic across replicas.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

from sqlalchemy import (
    Column,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from seismobrain_core.ingestion_jobs import (
    INGEST_JOB,
    IngestionJob,
    IngestionSummary,
    JobAction,
    JobConflict,
    JobEvent,
    JobPage,
    JobStatus,
    JobStopped,
    allowed_actions,
)

metadata = MetaData()
jobs = Table(
    "ingestion_jobs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("status", String(32), nullable=False),
    Column("collection_id", String(255), nullable=False),
    Column("filename", Text, nullable=False),
    Column("created_at", Float, nullable=False),
    Column("available_at", Float, nullable=False, default=0),
    Column("dispatch_until", Float, nullable=False, default=0),
    Column("lease_until", Float, nullable=False, default=0),
    Column("owner", String(64), nullable=False, default=""),
    Column("payload", Text, nullable=False),
    Column("record", Text, nullable=False),
    Index("ix_ingestion_jobs_pending", "status", "available_at"),
    Index("ix_ingestion_jobs_list", "name", "collection_id", "created_at"),
)
mutex = Table("ingestion_job_mutex", metadata, Column("id", Integer, primary_key=True))

checkpoints = Table(
    "ingestion_stage_checkpoints",
    metadata,
    Column("job_id", String(64), primary_key=True),
    Column("stage", String(64), primary_key=True),
    Column("attempts", Integer, nullable=False, default=0),
    Column("completed", Integer, nullable=False, default=0),
    Column("dead_letter", Integer, nullable=False, default=0),
)


class ClaimedJob(IngestionJob):
    owner: str
    payload: dict[str, Any]


class SqlJobStore:
    def __init__(self, database_url: str, *, retry_delay: float = 1, lease_seconds: float = 30):
        from seismobrain_adapters.metadata.postgres import _normalize_postgres_url

        self.engine = create_engine(_normalize_postgres_url(database_url))
        metadata.create_all(self.engine)
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(mutex).values(id=1))
        except IntegrityError:
            pass
        self.retry_delay = retry_delay
        self.lease_seconds = lease_seconds

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        with self.engine.begin() as conn:
            conn.execute(update(mutex).where(mutex.c.id == 1).values(id=1))
            yield conn

    def _get(self, conn: Connection, job_id: str) -> IngestionJob:
        raw = conn.execute(select(jobs.c.record).where(jobs.c.id == job_id)).scalar_one_or_none()
        if raw is None:
            raise KeyError(job_id)
        job = IngestionJob.model_validate_json(raw)
        job.actions = (
            []
            if job.status == "running" and job.stage == "INDEXED"
            else allowed_actions(job.status)
        )
        return job

    def _save(self, conn: Connection, job: IngestionJob, **extra: Any) -> None:
        job.updated_at = time.time()
        conn.execute(
            update(jobs)
            .where(jobs.c.id == job.id)
            .values(
                record=job.model_dump_json(),
                status=job.status,
                available_at=job.next_attempt_at,
                **extra,
            )
        )

    def _event(self, job: IngestionJob, status: str, **kwargs: Any) -> None:
        job.events.append(
            JobEvent(
                stage=job.stage,
                status=status,
                timestamp=time.time(),
                attempt=job.attempts,
                **kwargs,
            )
        )

    def enqueue(
        self,
        name: str,
        payload: Mapping[str, object],
        *,
        job_id: str | None = None,
        legacy_status: JobStatus | None = None,
        created_at: float | None = None,
    ) -> IngestionJob:
        import json

        now = created_at or time.time()
        job = IngestionJob(
            id=job_id or str(uuid.uuid4()),
            name=name,
            document_id=str(payload.get("document_id", "")),
            collection_id=str(payload.get("collection_id", "")),
            version_id=str(payload.get("version_id", f"{payload.get('document_id', '')}:v1")),
            filename=str(payload.get("filename", "")),
            created_at=now,
            updated_at=now,
            status=legacy_status or "pending",
            history_available=legacy_status is None,
        )
        if legacy_status is None:
            self._event(job, "queued")
        elif legacy_status == "running":
            job.status = "pending"
        else:
            job.stage = "UNKNOWN"
        with self.transaction() as conn:
            if conn.execute(select(jobs.c.id).where(jobs.c.id == job.id)).first():
                return self._get(conn, job.id)
            conn.execute(
                insert(jobs).values(
                    id=job.id,
                    name=name,
                    status=job.status,
                    collection_id=job.collection_id,
                    filename=job.filename,
                    created_at=now,
                    payload=json.dumps(dict(payload)),
                    record=job.model_dump_json(),
                )
            )
        return job

    def get(self, job_id: str) -> IngestionJob:
        with self.engine.connect() as conn:
            return self._get(conn, job_id)

    def page(
        self,
        *,
        status: JobStatus | None = None,
        collection_id: str = "",
        search: str = "",
        offset: int = 0,
        limit: int = 25,
    ) -> JobPage:
        terms = [jobs.c.name == INGEST_JOB]
        if status:
            terms.append(jobs.c.status == status)
        if collection_id:
            terms.append(jobs.c.collection_id == collection_id)
        if search:
            terms.append(jobs.c.filename.icontains(search, autoescape=True))
        with self.engine.connect() as conn:
            total = conn.execute(select(func.count()).select_from(jobs).where(*terms)).scalar_one()
            rows = conn.execute(
                select(jobs.c.record)
                .where(*terms)
                .order_by(
                    jobs.c.created_at.desc(),
                    jobs.c.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).scalars()
            result = [IngestionJob.model_validate_json(row) for row in rows]
        for job in result:
            job.actions = (
                []
                if job.status == "running" and job.stage == "INDEXED"
                else allowed_actions(job.status)
            )
            job.events = []  # Full history is available from the detail endpoint only.
            job.checkpoints = {}
        return JobPage(jobs=result, total=total, offset=offset, limit=limit)

    def summary(self) -> IngestionSummary:
        result = IngestionSummary(updated_at=time.time())
        with self.engine.connect() as conn:
            counts = {
                str(row[0]): int(row[1])
                for row in conn.execute(
                    select(jobs.c.status, func.count())
                    .where(
                        jobs.c.name == INGEST_JOB,
                    )
                    .group_by(jobs.c.status)
                ).all()
            }
            result.queue_depth = counts.pop("pending", 0)
            for key, count in counts.items():
                setattr(result, key, count)
            for raw in conn.execute(
                select(jobs.c.record).where(
                    jobs.c.name == INGEST_JOB,
                    jobs.c.status == "running",
                )
            ).scalars():
                stage = IngestionJob.model_validate_json(raw).stage
                result.stages[stage] = result.stages.get(stage, 0) + 1
        return result

    def due(self, *, dispatch: bool = False) -> list[str]:
        with self.transaction() as conn:
            now = time.time()
            terms = [jobs.c.status == "pending", jobs.c.available_at <= now]
            if dispatch:
                terms.append(jobs.c.dispatch_until <= now)
            ids = list(
                conn.execute(
                    select(jobs.c.id)
                    .where(*terms)
                    .order_by(
                        jobs.c.created_at,
                        jobs.c.id,
                    )
                    .limit(100)
                ).scalars()
            )
            if dispatch and ids:
                conn.execute(update(jobs).where(jobs.c.id.in_(ids)).values(dispatch_until=now + 2))
            return ids

    def active(self) -> bool:
        with self.engine.connect() as conn:
            return (
                conn.execute(
                    select(jobs.c.id)
                    .where(
                        jobs.c.status.in_(["pending", "running"]),
                    )
                    .limit(1)
                ).first()
                is not None
            )

    def claim(
        self,
        job_id: str,
        *,
        global_limit: int | None = None,
        per_collection_limit: int | None = None,
    ) -> ClaimedJob | None:
        import json

        with self.transaction() as conn:
            job = self._get(conn, job_id)
            if job.status != "pending" or job.next_attempt_at > time.time():
                return None
            running = select(func.count()).select_from(jobs).where(jobs.c.owner != "")
            if global_limit and conn.execute(running).scalar_one() >= global_limit:
                return None
            if (
                per_collection_limit
                and conn.execute(
                    running.where(
                        jobs.c.collection_id == job.collection_id,
                    )
                ).scalar_one()
                >= per_collection_limit
            ):
                return None
            job.status = "running"
            job.started_at = time.time()
            job.ended_at = None
            job.attempts += 1
            job.cycle_attempts += 1
            job.error = None
            job.stage = "STARTING"
            owner = str(uuid.uuid4())
            self._event(job, "started")
            self._save(conn, job, owner=owner, lease_until=time.time() + self.lease_seconds)
            payload = conn.execute(select(jobs.c.payload).where(jobs.c.id == job_id)).scalar_one()
            return ClaimedJob(**job.model_dump(), owner=owner, payload=json.loads(payload))

    def _owned(self, conn: Connection, job_id: str, owner: str) -> IngestionJob:
        row = conn.execute(
            select(jobs.c.owner, jobs.c.lease_until).where(
                jobs.c.id == job_id,
            )
        ).one()
        job = self._get(conn, job_id)
        if row.owner != owner or row.lease_until < time.time() or job.status != "running":
            raise JobStopped("Job is no longer owned by this worker")
        return job

    def heartbeat(self, job_id: str, owner: str) -> None:
        with self.transaction() as conn:
            conn.execute(
                update(jobs)
                .where(
                    jobs.c.id == job_id, jobs.c.owner == owner, jobs.c.lease_until >= time.time()
                )
                .values(
                    lease_until=time.time() + self.lease_seconds,
                )
            )

    @contextmanager
    def stage(self, job_id: str, owner: str, stage: str) -> Iterator[dict[str, int]]:
        started = time.monotonic()
        with self.transaction() as conn:
            job = self._owned(conn, job_id, owner)
            job.stage = stage
            self._event(job, "started")
            self._save(conn, job)
        counts: dict[str, int] = {}
        try:
            yield counts
        except Exception:
            with self.transaction() as conn:
                try:
                    job = self._owned(conn, job_id, owner)
                except JobStopped:
                    pass
                else:
                    self._event(
                        job,
                        "failed",
                        error=f"{stage} failed",
                        duration_ms=(time.monotonic() - started) * 1000,
                    )
                    self._save(conn, job)
            raise
        else:
            with self.transaction() as conn:
                job = self._owned(conn, job_id, owner)
                job.checkpoints[stage] = counts
                self._event(
                    job, "succeeded", counts=counts, duration_ms=(time.monotonic() - started) * 1000
                )
                self._save(conn, job)

    @contextmanager
    def publication(self, job_id: str, owner: str) -> Iterator[None]:
        # Serialize the final atomic index replacement with quarantine/ownership changes.
        with self.transaction() as conn:
            self._owned(conn, job_id, owner)
            yield

    def finish(self, job_id: str, owner: str, *, error: str | None = None) -> None:
        with self.transaction() as conn:
            job = self._get(conn, job_id)
            actual = conn.execute(select(jobs.c.owner).where(jobs.c.id == job_id)).scalar_one()
            if actual != owner:
                return
            lease_until = conn.execute(
                select(jobs.c.lease_until).where(jobs.c.id == job_id)
            ).scalar_one()
            if lease_until < time.time():
                error = "Worker lease expired before completion; the job must be replayed."
            if job.status == "quarantined":
                self._save(conn, job, owner="", lease_until=0)
                return
            if error:
                job.error = error
                job.status = "pending" if job.cycle_attempts < 3 else "dead_letter"
                # Generic jobs preserve their historical single-attempt behavior.
                if job.name != INGEST_JOB:
                    job.status = "failed"
                job.next_attempt_at = time.time() + self.retry_delay * 2 ** (job.cycle_attempts - 1)
                self._event(job, job.status, error=error)
            else:
                job.status = "succeeded"
                job.stage = "READY"
                self._event(job, "succeeded")
            job.ended_at = time.time()
            self._save(conn, job, owner="", lease_until=0, dispatch_until=0)

    def reclaim(self) -> int:
        count = 0
        with self.transaction() as conn:
            ids = list(
                conn.execute(
                    select(jobs.c.id).where(
                        jobs.c.owner != "",
                        jobs.c.lease_until < time.time(),
                    )
                ).scalars()
            )
            for job_id in ids:
                job = self._get(conn, job_id)
                if job.status == "running":
                    job.status = "pending" if job.cycle_attempts < 3 else "dead_letter"
                    job.error = "Worker stopped before completing the job"
                    job.ended_at = time.time()
                    self._event(job, "interrupted", error=job.error)
                self._save(conn, job, owner="", lease_until=0, dispatch_until=0)
                count += 1
        return count

    def action(
        self,
        job_id: str,
        action: JobAction,
        *,
        actor: str,
        reason: str = "",
    ) -> IngestionJob:
        with self.transaction() as conn:
            job = self._get(conn, job_id)
            if action == "quarantine" and job.status == "running" and job.stage == "INDEXED":
                raise JobConflict("Index publication is in progress; quarantine is unavailable")
            if action not in allowed_actions(job.status):
                raise JobConflict(f"Cannot {action} a {job.status} job")
            owner = conn.execute(select(jobs.c.owner).where(jobs.c.id == job_id)).scalar_one()
            if action == "release" and owner:
                raise JobConflict("Worker is stopping; release once it has stopped")
            if action == "quarantine":
                if not reason.strip():
                    raise JobConflict("A quarantine reason is required")
                job.status = "quarantined"
                job.quarantine_reason = reason.strip()
            else:
                job.status = "pending"
                job.stage = "QUEUED"
                job.cycle_attempts = 0
                job.next_attempt_at = 0
                job.error = None
                job.quarantine_reason = None
                job.ended_at = None
            self._event(job, action, actor=actor, reason=reason.strip() or None)
            self._save(conn, job, dispatch_until=0)
            job.actions = allowed_actions(job.status)
            return job
