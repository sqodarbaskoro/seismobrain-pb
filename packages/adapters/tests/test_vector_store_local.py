"""
File: test_vector_store_local.py
Description: Qdrant local-mode Starter VectorStore adapter tests
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

from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_core.ports import VectorPoint, VectorStore

_COLLECTION = "seismobrain_chunks_v1"
_DIM = 4


def test_local_store_satisfies_port_and_writes_under_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    store: VectorStore = QdrantLocalVectorStore(data_dir)
    store.ensure_collection(_COLLECTION, vector_size=_DIM)
    assert store.count(_COLLECTION) == 0

    point = VectorPoint(
        id="11111111-1111-1111-1111-111111111111",
        vector=[0.1, 0.2, 0.3, 0.4],
        payload={"tenant_id": "t1", "document_id": "d1", "is_latest": True},
    )
    store.upsert(_COLLECTION, [point])
    assert store.count(_COLLECTION) == 1

    hits = store.search(_COLLECTION, query_vector=point.vector, limit=5)
    assert len(hits) == 1
    assert hits[0].id == point.id
    assert hits[0].payload["tenant_id"] == "t1"

    qdrant_path = data_dir / "qdrant"
    assert qdrant_path.is_dir()
    assert any(qdrant_path.iterdir()), "local mode must persist under DATA_DIR/qdrant"


def test_local_store_persists_across_instances(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    first = QdrantLocalVectorStore(data_dir)
    first.ensure_collection(_COLLECTION, vector_size=_DIM)
    first.upsert(
        _COLLECTION,
        [
            VectorPoint(
                id="22222222-2222-2222-2222-222222222222",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={"tenant_id": "t1"},
            )
        ],
    )
    # Release local lock before reopening the same path.
    first.close()
    second = QdrantLocalVectorStore(data_dir)
    assert second.count(_COLLECTION) == 1
    second.close()
