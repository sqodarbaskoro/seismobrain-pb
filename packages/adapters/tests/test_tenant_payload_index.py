"""
File: test_tenant_payload_index.py
Description: FR-IDX-07 / SEC-24 — tenant_id payload index with is_tenant true
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

_QDRANT_IMAGE = "qdrant/qdrant:v1.19.1"
_COLLECTION = "seismobrain_chunks_v1"


@pytest.fixture(scope="module")
def qdrant_url() -> Iterator[str]:
    with QdrantContainer(_QDRANT_IMAGE) as container:
        yield f"http://{container.rest_host_address}"


def test_tenant_id_payload_index_has_is_tenant_true(qdrant_url: str) -> None:
    assert REQUIRED_PAYLOAD_INDEXES["tenant_id"].is_tenant is True
    store = QdrantServerVectorStore(url=qdrant_url)
    try:
        store.ensure_collection(_COLLECTION, vector_size=4)
        schema = store.payload_schema(_COLLECTION)
        assert "tenant_id" in schema
        assert schema["tenant_id"]["data_type"] == "keyword"
        assert schema["tenant_id"]["is_tenant"] is True
    finally:
        store.close()
