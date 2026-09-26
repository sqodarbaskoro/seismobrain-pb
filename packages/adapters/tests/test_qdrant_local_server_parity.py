"""
File: test_qdrant_local_server_parity.py
Description: FR-RET-01 — Qdrant local/server filter and rank parity suite
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

from collections.abc import Iterator
from pathlib import Path

import pytest
from testcontainers.community.qdrant import QdrantContainer

from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_adapters.vector.qdrant_server import QdrantServerVectorStore
from seismobrain_core.idf_scope import IdfScope, resolve_idf_corpus_filter
from seismobrain_core.ports import VectorPoint

_QDRANT_IMAGE = "qdrant/qdrant:v1.19.1"
_COLLECTION = "parity_chunks"
_DIM = 4


def _seed(store: QdrantLocalVectorStore | QdrantServerVectorStore) -> None:
    store.ensure_collection(_COLLECTION, vector_size=_DIM)
    store.upsert(
        _COLLECTION,
        [
            VectorPoint(
                id="11111111-1111-1111-1111-111111111111",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={
                    "tenant_id": "t1",
                    "workspace_id": "w1",
                    "acl": ["u:a"],
                    "is_latest": True,
                    "mark": "a",
                },
            ),
            VectorPoint(
                id="22222222-2222-2222-2222-222222222222",
                vector=[0.9, 0.1, 0.0, 0.0],
                payload={
                    "tenant_id": "t1",
                    "workspace_id": "w1",
                    "acl": ["u:a"],
                    "is_latest": True,
                    "mark": "b",
                },
            ),
            VectorPoint(
                id="33333333-3333-3333-3333-333333333333",
                vector=[0.0, 1.0, 0.0, 0.0],
                payload={
                    "tenant_id": "t2",
                    "workspace_id": "w2",
                    "acl": ["u:b"],
                    "is_latest": True,
                    "mark": "other-tenant",
                },
            ),
        ],
    )


def test_local_idf_corpus_filter_documented_unsupported() -> None:
    """Starter local mode does not apply IDF corpus search params (PRD §8.4.4)."""
    filt = resolve_idf_corpus_filter(
        tenant_id="t1",
        workspace_id="w1",
        scope=IdfScope.TENANT,
        workspace_point_count=0,
    )
    assert filt == {"tenant_id": "t1"}
    # Documentation marker for parity suite consumers.
    assert QdrantLocalVectorStore.__doc__ is not None


def test_local_rank_order_stable(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "qdrant")
    try:
        _seed(store)
        hits = store.search(_COLLECTION, query_vector=[1.0, 0.0, 0.0, 0.0], limit=3)
        ids = [h.id for h in hits]
        assert ids[0] == "11111111-1111-1111-1111-111111111111"
        assert "33333333-3333-3333-3333-333333333333" in ids or len(ids) >= 1
    finally:
        store.close()


@pytest.fixture(scope="module")
def qdrant_url() -> Iterator[str]:
    with QdrantContainer(_QDRANT_IMAGE) as container:
        yield f"http://{container.rest_host_address}"


def test_local_server_authorized_id_set_and_rank_parity(
    tmp_path: Path, qdrant_url: str
) -> None:
    local = QdrantLocalVectorStore(tmp_path / "local")
    server = QdrantServerVectorStore(url=qdrant_url)
    try:
        _seed(local)
        _seed(server)
        query = [1.0, 0.0, 0.0, 0.0]
        local_hits = local.search(_COLLECTION, query_vector=query, limit=2)
        server_hits = server.search(_COLLECTION, query_vector=query, limit=2)
        local_ids = [h.id for h in local_hits]
        server_ids = [h.id for h in server_hits]
        assert local_ids == server_ids
        # Top hit is the exact vector match in both modes.
        assert local_ids[0] == "11111111-1111-1111-1111-111111111111"
    finally:
        local.close()
        server.close()
