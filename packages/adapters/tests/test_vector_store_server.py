"""
File: test_vector_store_server.py
Description: Qdrant server Team VectorStore adapter tests (testcontainers)
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

import pytest
from testcontainers.community.qdrant import QdrantContainer

from seismobrain_adapters.vector.payload_indexes import REQUIRED_PAYLOAD_INDEXES
from seismobrain_adapters.vector.qdrant_server import QdrantServerVectorStore
from seismobrain_core.ports import VectorPoint, VectorStore

# Pin per PRD (Qdrant ≥ 1.19); never use :latest.
_QDRANT_IMAGE = "qdrant/qdrant:v1.19.1"
_COLLECTION = "seismobrain_chunks_v1"
_DIM = 4


@pytest.fixture(scope="module")
def qdrant_url() -> Iterator[str]:
    with QdrantContainer(_QDRANT_IMAGE) as container:
        # rest_host_address is "host:port"; QdrantClient expects an http(s) URL or host+port.
        yield f"http://{container.rest_host_address}"


@pytest.fixture
def store(qdrant_url: str) -> Iterator[QdrantServerVectorStore]:
    vs = QdrantServerVectorStore(url=qdrant_url)
    yield vs
    vs.close()


def test_server_store_satisfies_port(store: QdrantServerVectorStore) -> None:
    port: VectorStore = store
    port.ensure_collection(_COLLECTION, vector_size=_DIM)
    assert port.count(_COLLECTION) == 0
    point = VectorPoint(
        id="33333333-3333-3333-3333-333333333333",
        vector=[0.0, 1.0, 0.0, 0.0],
        payload={"tenant_id": "t1", "is_latest": True},
    )
    port.upsert(_COLLECTION, [point])
    assert port.count(_COLLECTION) == 1
    hits = port.search(_COLLECTION, query_vector=point.vector, limit=3)
    assert hits[0].id == point.id


def test_collection_bootstrap_creates_required_payload_indexes(
    store: QdrantServerVectorStore,
) -> None:
    store.ensure_collection(_COLLECTION, vector_size=_DIM)
    schema = store.payload_schema(_COLLECTION)
    for field_name, expected in REQUIRED_PAYLOAD_INDEXES.items():
        assert field_name in schema, f"missing payload index: {field_name}"
        actual = schema[field_name]
        assert actual["data_type"] == expected.data_type
        if expected.is_tenant:
            assert actual.get("is_tenant") is True, "tenant_id must use is_tenant: true"
