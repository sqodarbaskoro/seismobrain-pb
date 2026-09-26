"""Starter queue: durable SQLite records and safe import of legacy JSON jobs."""

from __future__ import annotations

import json
from pathlib import Path

from seismobrain_adapters.queue.durable import DurableQueue
from seismobrain_adapters.queue.job_store import SqlJobStore


class InProcessJobQueue(DurableQueue):
    def __init__(
        self,
        storage_dir: Path | str,
        *,
        workers: int = 1,
        global_limit: int | None = None,
        per_collection_limit: int | None = None,
    ) -> None:
        root = Path(storage_dir)
        root.mkdir(parents=True, exist_ok=True)
        super().__init__(
            SqlJobStore(f"sqlite:///{root / 'jobs.db'}"),
            global_limit=global_limit,
            per_collection_limit=per_collection_limit,
        )
        self._workers = max(1, workers)
        for path in sorted(root.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            self.store.enqueue(
                record["name"],
                record["payload"],
                job_id=record["id"],
                legacy_status=record["status"],
                created_at=path.stat().st_mtime,
            )
