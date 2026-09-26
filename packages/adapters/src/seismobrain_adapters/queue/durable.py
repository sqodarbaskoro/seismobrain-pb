"""Shared durable queue lifecycle for local and broker-backed execution."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Mapping
from contextlib import AbstractContextManager

from seismobrain_adapters.queue.job_store import SqlJobStore
from seismobrain_core.ingestion_jobs import (
    IngestionJob,
    IngestionSummary,
    JobAction,
    JobPage,
    JobStatus,
    JobStopped,
)
from seismobrain_core.job_execution import current_execution
from seismobrain_core.ports import JobHandler

logger = logging.getLogger(__name__)


class StoreExecution:
    def __init__(self, store: SqlJobStore, job_id: str, owner: str):
        self.store, self.job_id, self.owner = store, job_id, owner

    def stage(self, name: str) -> AbstractContextManager[dict[str, int]]:
        return self.store.stage(self.job_id, self.owner, name)

    def publication(self) -> AbstractContextManager[None]:
        return self.store.publication(self.job_id, self.owner)


def safe_error(exc: Exception) -> str:
    # Exception strings can contain source text, credentials, or paths. Store only
    # a known classification; the failed stage supplies the operational context.
    if isinstance(exc, FileNotFoundError):
        return "Source file is missing. Restore the uploaded file before retrying."
    if isinstance(exc, PermissionError):
        return "Source or index access was denied. Check storage permissions."
    if isinstance(exc, ValueError):
        return "Document processing rejected the input. Check its format and contents."
    return f"{type(exc).__name__}: processing failed. Check the source and service configuration."


class DurableQueue:
    def __init__(
        self,
        store: SqlJobStore,
        *,
        global_limit: int | None = None,
        per_collection_limit: int | None = None,
    ) -> None:
        if global_limit is not None and global_limit < 1:
            raise ValueError("global_limit must be >= 1")
        if per_collection_limit is not None and per_collection_limit < 1:
            raise ValueError("per_collection_limit must be >= 1")
        self.store = store
        self._handlers: dict[str, JobHandler] = {}
        self._global_limit = global_limit
        self._per_collection_limit = per_collection_limit

    def register(self, name: str, handler: JobHandler) -> None:
        self._handlers[name] = handler

    def enqueue(self, name: str, payload: Mapping[str, object]) -> str:
        return self.store.enqueue(name, payload).id

    def get_status(self, job_id: str) -> str:
        try:
            return self.store.get(job_id).status
        except KeyError:
            return "missing"

    def get_job(self, job_id: str) -> IngestionJob:
        return self.store.get(job_id)

    def summary(self) -> IngestionSummary:
        return self.store.summary()

    def depth(self) -> int:
        return self.summary().queue_depth

    def list_jobs(
        self,
        *,
        status: JobStatus | None = None,
        collection_id: str = "",
        search: str = "",
        offset: int = 0,
        limit: int = 25,
    ) -> JobPage:
        return self.store.page(
            status=status, collection_id=collection_id, search=search, offset=offset, limit=limit
        )

    def job_action(
        self,
        job_id: str,
        action: JobAction,
        *,
        actor: str,
        reason: str = "",
    ) -> IngestionJob:
        return self.store.action(job_id, action, actor=actor, reason=reason)

    def reclaim_interrupted(self) -> int:
        return self.store.reclaim()

    def _execute(self, job_id: str) -> None:
        claim = self.store.claim(
            job_id, global_limit=self._global_limit, per_collection_limit=self._per_collection_limit
        )
        if claim is None:
            return
        stop = threading.Event()

        def heartbeat() -> None:
            while not stop.wait(self.store.lease_seconds / 3):
                try:
                    self.store.heartbeat(job_id, claim.owner)
                except Exception:
                    logger.error("Ingestion lease renewal failed for job %s", job_id)
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        token = current_execution.set(StoreExecution(self.store, job_id, claim.owner))
        error: str | None = None
        try:
            handler = self._handlers.get(claim.name)
            if handler is None:
                error = "No worker handler is registered for this job type."
            else:
                handler(claim.payload)
        except JobStopped:
            error = "Processing stopped because job ownership or quarantine changed."
        except Exception as exc:
            error = safe_error(exc)
        finally:
            current_execution.reset(token)
            stop.set()
            thread.join()
        self.store.finish(job_id, claim.owner, error=error)

    def run_pending(self, timeout_seconds: float = 5.0) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self.store.reclaim()
            for job_id in self.store.due():
                if time.monotonic() >= deadline:
                    break
                self._execute(job_id)
            if not self.store.active():
                return
            time.sleep(0.05)

    def close(self) -> None:
        self.store.engine.dispose()
