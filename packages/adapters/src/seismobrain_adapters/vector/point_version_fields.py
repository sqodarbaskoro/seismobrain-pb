"""
File: point_version_fields.py
Description: Point and index-version stamp fields for FR-IDX-02
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

from dataclasses import dataclass
from typing import Any

REQUIRED_POINT_VERSION_FIELDS = (
    "pipeline_version",
    "embedding_model",
    "embedding_revision",
    "sparse_encoder",
    "chunker_version",
    "source_hash",
    "document_version",
    "text_hash",
)


@dataclass(frozen=True, slots=True)
class PointVersionFields:
    pipeline_version: str
    embedding_model: str
    embedding_revision: str
    sparse_encoder: str
    chunker_version: str
    source_hash: str
    document_version: str
    text_hash: str

    def to_payload(self) -> dict[str, str]:
        return {
            "pipeline_version": self.pipeline_version,
            "embedding_model": self.embedding_model,
            "embedding_revision": self.embedding_revision,
            "sparse_encoder": self.sparse_encoder,
            "chunker_version": self.chunker_version,
            "source_hash": self.source_hash,
            "document_version": self.document_version,
            "text_hash": self.text_hash,
        }


@dataclass(frozen=True, slots=True)
class IndexVersionRecord:
    physical_name: str
    embedding_model: str
    embedding_revision: str
    sparse_encoder: str
    bm25_k1: float
    bm25_b: float
    bm25_avg_len: float
    chunker_version: str
    qdrant_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "physical_name": self.physical_name,
            "embedding_model": self.embedding_model,
            "embedding_revision": self.embedding_revision,
            "sparse_encoder": self.sparse_encoder,
            "bm25_k1": self.bm25_k1,
            "bm25_b": self.bm25_b,
            "bm25_avg_len": self.bm25_avg_len,
            "chunker_version": self.chunker_version,
            "qdrant_version": self.qdrant_version,
        }


def validate_point_version_payload(payload: dict[str, Any]) -> PointVersionFields:
    for field in REQUIRED_POINT_VERSION_FIELDS:
        if field not in payload:
            raise ValueError(f"missing required point field: {field}")
        value = payload[field]
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field} must be a non-empty string")
    return PointVersionFields(
        pipeline_version=payload["pipeline_version"],
        embedding_model=payload["embedding_model"],
        embedding_revision=payload["embedding_revision"],
        sparse_encoder=payload["sparse_encoder"],
        chunker_version=payload["chunker_version"],
        source_hash=payload["source_hash"],
        document_version=payload["document_version"],
        text_hash=payload["text_hash"],
    )


def validate_index_version_record(record: IndexVersionRecord) -> None:
    if not record.physical_name:
        raise ValueError("physical_name required")
    if not record.qdrant_version:
        raise ValueError("qdrant_version required")
    if record.bm25_k1 <= 0 or record.bm25_b < 0 or record.bm25_avg_len <= 0:
        raise ValueError("invalid BM25 parameters")
