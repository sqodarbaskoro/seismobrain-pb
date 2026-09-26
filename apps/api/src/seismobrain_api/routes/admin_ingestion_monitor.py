"""Administrator monitoring and recovery backed by durable ingestion jobs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_core.ingestion_jobs import (
    INGEST_JOB,
    IngestionJob,
    IngestionMonitor,
    IngestionSummary,
    JobAction,
    JobConflict,
    JobPage,
    JobStatus,
)

router = APIRouter(prefix="/api/v1/admin/ingestion", tags=["admin-ingestion"])


class QuarantineRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


@contextmanager
def _monitor(request: Request) -> Iterator[IngestionMonitor]:
    require_admin(request)
    queue = cast(AppContainer, request.app.state.container).job_queue
    if not isinstance(queue, IngestionMonitor):
        raise HTTPException(status_code=503, detail="Ingestion monitoring is unavailable")
    try:
        yield queue
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ingestion job not found") from exc
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (SQLAlchemyError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Ingestion job storage is unavailable") from exc


def _job(monitor: IngestionMonitor, job_id: str) -> IngestionJob:
    job = monitor.get_job(job_id)
    if job.name != INGEST_JOB:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job


@router.get("/monitor")
def ingestion_monitor(request: Request) -> IngestionSummary:
    with _monitor(request) as monitor:
        return monitor.summary()


@router.get("/jobs")
def list_jobs(
    request: Request,
    status: JobStatus | None = None,
    collection_id: Annotated[str, Query(max_length=255)] = "",
    search: Annotated[str, Query(max_length=255)] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> JobPage:
    with _monitor(request) as monitor:
        return monitor.list_jobs(
            status=status, collection_id=collection_id, search=search, offset=offset, limit=limit
        )


@router.get("/jobs/{job_id}")
def job_detail(job_id: str, request: Request) -> IngestionJob:
    with _monitor(request) as monitor:
        return _job(monitor, job_id)


def _action(request: Request, job_id: str, action: JobAction, reason: str = "") -> IngestionJob:
    principal = require_admin(request)
    with _monitor(request) as monitor:
        _job(monitor, job_id)
        return monitor.job_action(job_id, action, actor=principal.user_id, reason=reason)


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, request: Request) -> IngestionJob:
    return _action(request, job_id, "retry")


@router.post("/jobs/{job_id}/quarantine")
def quarantine_job(job_id: str, body: QuarantineRequest, request: Request) -> IngestionJob:
    return _action(request, job_id, "quarantine", body.reason)


@router.post("/jobs/{job_id}/release")
def release_job(job_id: str, request: Request) -> IngestionJob:
    return _action(request, job_id, "release")
