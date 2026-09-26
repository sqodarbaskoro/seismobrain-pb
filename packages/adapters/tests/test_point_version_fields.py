"""
File: test_point_version_fields.py
Description: FR-IDX-02 — point and index version stamp fields
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

from seismobrain_adapters.vector.point_version_fields import (
    REQUIRED_POINT_VERSION_FIELDS,
    IndexVersionRecord,
    PointVersionFields,
    validate_index_version_record,
    validate_point_version_payload,
)
from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_core.ports import VectorPoint


def test_required_point_fields_listed() -> None:
    assert REQUIRED_POINT_VERSION_FIELDS == (
        "pipeline_version",
        "embedding_model",
        "embedding_revision",
        "sparse_encoder",
        "chunker_version",
        "source_hash",
        "document_version",
        "text_hash",
    )


def test_point_upsert_stores_version_fields(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    store.ensure_collection("seismobrain_chunks_v1", vector_size=4)
    stamps = PointVersionFields(
        pipeline_version="pipe-1",
        embedding_model="cpu-hash",
        embedding_revision="rev1",
        sparse_encoder="id-bm25@1",
        chunker_version="chunker-v1",
        source_hash="src-abc",
        document_version="ver-1",
        text_hash="texthash1",
    )
    point = VectorPoint(
        id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        vector=[0.1, 0.2, 0.3, 0.4],
        payload=stamps.to_payload(),
    )
    store.upsert("seismobrain_chunks_v1", [point])
    hits = store.search(
        "seismobrain_chunks_v1", query_vector=point.vector, limit=1
    )
    validated = validate_point_version_payload(hits[0].payload)
    assert validated == stamps
    store.close()


def test_index_version_records_bm25_and_qdrant_version() -> None:
    record = IndexVersionRecord(
        physical_name="seismobrain_chunks_v1",
        embedding_model="cpu-hash",
        embedding_revision="rev1",
        sparse_encoder="id-bm25@1",
        bm25_k1=1.2,
        bm25_b=0.75,
        bm25_avg_len=120.0,
        chunker_version="chunker-v1",
        qdrant_version="1.19.1",
    )
    validate_index_version_record(record)
    data = record.to_dict()
    assert data["bm25_k1"] == 1.2
    assert data["bm25_b"] == 0.75
    assert data["bm25_avg_len"] == 120.0
    assert data["qdrant_version"] == "1.19.1"


def test_missing_point_field_rejected() -> None:
    with pytest.raises(ValueError, match="missing required point field"):
        validate_point_version_payload({"pipeline_version": "p1"})
