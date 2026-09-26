"""
File: qdrant_base.py
Description: Shared Qdrant VectorStore operations for local and server adapters
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

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from seismobrain_adapters.vector.payload_indexes import REQUIRED_PAYLOAD_INDEXES
from seismobrain_core.ports import VectorPoint

_SCHEMA_TYPE = {
    "keyword": qm.PayloadSchemaType.KEYWORD,
    "bool": qm.PayloadSchemaType.BOOL,
    "datetime": qm.PayloadSchemaType.DATETIME,
}


class QdrantVectorStoreBase:
    """Shared upsert/search/count/bootstrap for Qdrant-backed VectorStore adapters."""

    def __init__(self, client: QdrantClient, *, create_payload_indexes: bool) -> None:
        self._client = client
        self._create_payload_indexes = create_payload_indexes

    @property
    def client(self) -> QdrantClient:
        return self._client

    def ensure_collection(self, name: str, vector_size: int) -> None:
        if not self._client.collection_exists(name):
            self._client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(
                    size=vector_size, distance=qm.Distance.COSINE
                ),
            )
        if self._create_payload_indexes:
            self._ensure_payload_indexes(name)

    def _ensure_payload_indexes(self, collection: str) -> None:
        existing = self.payload_schema(collection)
        for field_name, spec in REQUIRED_PAYLOAD_INDEXES.items():
            if field_name in existing:
                continue
            if spec.is_tenant:
                field_schema: qm.PayloadSchemaType | qm.KeywordIndexParams = (
                    qm.KeywordIndexParams(
                        type=qm.KeywordIndexType.KEYWORD,
                        is_tenant=True,
                    )
                )
            else:
                field_schema = _SCHEMA_TYPE[spec.data_type]
            self._client.create_payload_index(
                collection_name=collection,
                field_name=field_name,
                field_schema=field_schema,
            )

    def payload_schema(self, collection: str) -> dict[str, dict[str, Any]]:
        info = self._client.get_collection(collection)
        raw = info.payload_schema or {}
        out: dict[str, dict[str, Any]] = {}
        for name, meta in raw.items():
            data_type = getattr(meta, "data_type", None)
            params = getattr(meta, "params", None)
            is_tenant = bool(getattr(params, "is_tenant", False)) if params else False
            out[name] = {
                "data_type": str(data_type.value) if data_type is not None else "",
                "is_tenant": is_tenant,
            }
        return out

    def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        self._client.upsert(
            collection_name=collection,
            points=[
                qm.PointStruct(id=p.id, vector=p.vector, payload=dict(p.payload))
                for p in points
            ],
        )

    def search(
        self, collection: str, query_vector: list[float], limit: int = 10
    ) -> list[VectorPoint]:
        hits = self._client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            with_payload=True,
        ).points
        return [
            VectorPoint(
                id=str(hit.id),
                vector=[],
                payload=dict(hit.payload) if hit.payload is not None else {},
            )
            for hit in hits
        ]

    def count(self, collection: str) -> int:
        return int(self._client.count(collection_name=collection, exact=True).count)

    def close(self) -> None:
        self._client.close()
