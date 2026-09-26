"""
File: test_index_alias.py
Description: FR-IDX-01 — physical collections via seismobrain_chunks_active alias
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

from seismobrain_adapters.vector.index_alias import (
    ACTIVE_ALIAS,
    physical_collection_name,
    resolve_active_collection,
    set_active_alias,
)
from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_core.ports import VectorPoint


def test_physical_collection_naming() -> None:
    assert physical_collection_name(1) == "seismobrain_chunks_v1"
    assert physical_collection_name(3) == "seismobrain_chunks_v3"
    assert ACTIVE_ALIAS == "seismobrain_chunks_active"


def test_active_alias_points_at_physical_collection(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    v1 = physical_collection_name(1)
    v2 = physical_collection_name(2)
    store.ensure_collection(v1, vector_size=4)
    store.ensure_collection(v2, vector_size=4)
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
    store.upsert(
        v2,
        [
            VectorPoint(
                id="22222222-2222-2222-2222-222222222222",
                vector=[0.0, 1.0, 0.0, 0.0],
                payload={"mark": "v2"},
            )
        ],
    )

    set_active_alias(store, v1)
    assert resolve_active_collection(store) == v1
    hits = store.search(ACTIVE_ALIAS, query_vector=[1.0, 0.0, 0.0, 0.0], limit=1)
    assert hits[0].payload.get("mark") == "v1"

    set_active_alias(store, v2)
    assert resolve_active_collection(store) == v2
    hits = store.search(ACTIVE_ALIAS, query_vector=[0.0, 1.0, 0.0, 0.0], limit=1)
    assert hits[0].payload.get("mark") == "v2"
    store.close()
