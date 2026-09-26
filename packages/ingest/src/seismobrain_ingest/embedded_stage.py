"""
File: embedded_stage.py
Description: EMBEDDED ingest stage — dense encode via ModelGateway with reuse/cache
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from seismobrain_core.embedding_reuse import (
    EmbedUnit,
    ResolvedEmbedding,
    compute_text_hash,
    resolve_embeddings,
)
from seismobrain_core.ports import EmbeddingCache, ModelGateway


class StageOrderError(RuntimeError):
    """Raised when INDEXED is attempted without a completed EMBEDDED stage."""


@dataclass(frozen=True, slots=True)
class ChunkToEmbed:
    chunk_id: str
    document_id: str
    embedded_text: str


@dataclass(frozen=True, slots=True)
class EmbeddedItem:
    chunk_id: str
    document_id: str
    text_hash: str
    vector: list[float]
    source: str


@dataclass(frozen=True, slots=True)
class EmbeddedStageResult:
    items: tuple[EmbeddedItem, ...]
    encode_calls: int
    encoded_texts: int


def require_embedded_before_index(*, embedded_completed: bool) -> None:
    """Fail closed: INDEXED must not run unless EMBEDDED completed."""
    if not embedded_completed:
        raise StageOrderError("EMBEDDED must complete before INDEXED")


def run_embedded_stage(
    chunks: Sequence[ChunkToEmbed],
    *,
    gateway: ModelGateway,
    cache: EmbeddingCache,
    index_lookup: Mapping[tuple[str, str, str], list[float]],
    model_id: str,
    model_revision: str,
) -> EmbeddedStageResult:
    """Batch-resolve dense vectors: index → cache → ModelGateway.embed."""
    units = [
        EmbedUnit(
            unit_id=c.chunk_id,
            document_id=c.document_id,
            embedded_text=c.embedded_text,
        )
        for c in chunks
    ]

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return gateway.embed(texts, model_id=model_id)

    resolved, encode_calls = resolve_embeddings(
        units,
        model_id=model_id,
        model_revision=model_revision,
        cache=cache,
        index_lookup=index_lookup,
        embed_fn=embed_fn,
    )
    items = tuple(
        EmbeddedItem(
            chunk_id=r.unit_id,
            document_id=r.document_id,
            text_hash=r.text_hash,
            vector=r.vector,
            source=r.source,
        )
        for r in resolved
    )
    encoded_texts = sum(1 for r in resolved if r.source == "encode")
    return EmbeddedStageResult(
        items=items, encode_calls=encode_calls, encoded_texts=encoded_texts
    )


__all__ = [
    "ChunkToEmbed",
    "EmbeddedItem",
    "EmbeddedStageResult",
    "StageOrderError",
    "compute_text_hash",
    "require_embedded_before_index",
    "run_embedded_stage",
    "ResolvedEmbedding",
]
