"""Dramatiq delivery with database-backed status, claims, and dispatch recovery."""

from __future__ import annotations

import time

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from seismobrain_adapters.queue.durable import DurableQueue
from seismobrain_adapters.queue.job_store import SqlJobStore


class DramatiqRedisJobQueue(DurableQueue):
    def __init__(self, redis_url: str, *, database_url: str) -> None:
        super().__init__(SqlJobStore(database_url))
        self._broker = RedisBroker(url=redis_url)  # type: ignore[no-untyped-call]

        @dramatiq.actor(broker=self._broker, actor_name="ingestion_dispatch", max_retries=0)
        def dispatch(job_id: str) -> None:
            self._execute(job_id)

        self._dispatch = dispatch
        self._worker: dramatiq.Worker | None = None

    def run_pending(self, timeout_seconds: float = 5.0) -> None:
        if self._worker is None:
            self._worker = dramatiq.Worker(self._broker, worker_threads=1)
            self._worker.start()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self.store.reclaim()
            # SQL is the durable outbox. Broker failure or lost messages are repaired
            # on the next pass; duplicate delivery cannot claim an already-owned job.
            for job_id in self.store.due(dispatch=True):
                self._dispatch.send(job_id)
            if not self.store.active():
                return
            time.sleep(0.05)

    def close(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker.join()
            self._worker = None
        self._broker.close()
        super().close()
