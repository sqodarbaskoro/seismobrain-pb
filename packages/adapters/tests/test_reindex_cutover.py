"""
File: test_reindex_cutover.py
Description: Re-index workflow alias cut-over (T5.25)
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

from pathlib import Path

import pytest

from seismobrain_adapters.vector.index_alias import (
    ACTIVE_ALIAS,
    physical_collection_name,
    resolve_active_collection,
    set_active_alias,
)
from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_adapters.vector.reindex_cutover import ReindexWorkflow
from seismobrain_core.ports import VectorPoint


def test_reindex_builds_evaluates_and_switches_atomically(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    v1 = physical_collection_name(1)
    store.ensure_collection(v1, vector_size=4)
    store.upsert(
        v1,
        [
            VectorPoint(
                id="11111111-1111-1111-1111-111111111111",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={"mark": "v1"},
            )
        ],
    )
    set_active_alias(store, v1)

    workflow = ReindexWorkflow(vector_size=4)
    result = workflow.run(
        store,
        [
            VectorPoint(
                id="22222222-2222-2222-2222-222222222222",
                vector=[0.0, 1.0, 0.0, 0.0],
                payload={"mark": "v2"},
            )
        ],
        metrics={"recall@10": 0.92},
        probe_query=[0.0, 1.0, 0.0, 0.0],
    )
    assert result.previous == v1
    assert result.active == physical_collection_name(2)
    assert result.kept_previous is True
    assert result.query_failures_during_switch == 0
    assert resolve_active_collection(store) == physical_collection_name(2)
    hits = store.search(ACTIVE_ALIAS, [0.0, 1.0, 0.0, 0.0], limit=1)
    assert hits[0].payload.get("mark") == "v2"
    # Previous physical collection still exists for rollback.
    assert store.count(v1) == 1
    store.close()


def test_reindex_rejects_failed_evaluation(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    workflow = ReindexWorkflow(vector_size=4, min_recall=0.9)
    with pytest.raises(ValueError, match="evaluation failed"):
        workflow.run(
            store,
            [],
            target="seismobrain_chunks_v-test",
            metrics={"recall@10": 0.5},
        )
    store.close()
