"""
File: reindex_cutover.py
Description: Re-index workflow with atomic alias cut-over (FR-IDX-03, FR-ADM-09)
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

from dataclasses import dataclass, field

from seismobrain_adapters.vector.index_alias import (
    ACTIVE_ALIAS,
    physical_collection_name,
    resolve_active_collection,
    set_active_alias,
)
from seismobrain_adapters.vector.qdrant_base import QdrantVectorStoreBase
from seismobrain_core.ports import VectorPoint


@dataclass
class ReindexResult:
    previous: str | None
    active: str
    evaluated: bool
    kept_previous: bool
    query_failures_during_switch: int = 0


@dataclass
class ReindexWorkflow:
    """Build next physical collection, evaluate, atomically switch alias."""

    vector_size: int = 4
    smoke_metrics: dict[str, float] = field(
        default_factory=lambda: {"recall@10": 0.95}
    )
    min_recall: float = 0.85

    def next_version_name(self, store: QdrantVectorStoreBase) -> str:
        current = resolve_active_collection(store)
        if current is None:
            return physical_collection_name(1)
        # seismobrain_chunks_vN → N+1
        try:
            version = int(current.rsplit("_v", 1)[-1])
        except ValueError:
            version = 1
        return physical_collection_name(version + 1)

    def build_next(
        self,
        store: QdrantVectorStoreBase,
        points: list[VectorPoint],
        *,
        target: str | None = None,
    ) -> str:
        name = target or self.next_version_name(store)
        store.ensure_collection(name, vector_size=self.vector_size)
        if points:
            store.upsert(name, points)
        return name

    def evaluate(self, metrics: dict[str, float] | None = None) -> bool:
        m = metrics if metrics is not None else self.smoke_metrics
        return float(m.get("recall@10", 0.0)) >= self.min_recall

    def cutover(
        self,
        store: QdrantVectorStoreBase,
        next_physical: str,
        *,
        probe_query: list[float] | None = None,
    ) -> ReindexResult:
        previous = resolve_active_collection(store)
        failures = 0
        # Probe through the alias before and after switch — must stay queryable.
        if probe_query is not None and previous is not None:
            try:
                store.search(ACTIVE_ALIAS, probe_query, limit=1)
            except Exception:
                failures += 1
        set_active_alias(store, next_physical)
        if probe_query is not None:
            try:
                store.search(ACTIVE_ALIAS, probe_query, limit=1)
            except Exception:
                failures += 1
        return ReindexResult(
            previous=previous,
            active=next_physical,
            evaluated=True,
            kept_previous=previous is not None and previous != next_physical,
            query_failures_during_switch=failures,
        )

    def run(
        self,
        store: QdrantVectorStoreBase,
        points: list[VectorPoint],
        *,
        target: str | None = None,
        metrics: dict[str, float] | None = None,
        probe_query: list[float] | None = None,
    ) -> ReindexResult:
        next_name = self.build_next(store, points, target=target)
        if not self.evaluate(metrics):
            raise ValueError("reindex evaluation failed; alias not switched")
        return self.cutover(store, next_name, probe_query=probe_query)
