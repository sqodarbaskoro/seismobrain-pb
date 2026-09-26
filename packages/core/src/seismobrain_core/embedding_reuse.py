"""
File: embedding_reuse.py
Description: Embedding reuse keyed by text_hash + model identity (FR-IDX-04, §8.4.5)
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

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol


class EmbeddingCacheLike(Protocol):
    def get(
        self, text_hash: str, model_id: str, model_revision: str
    ) -> list[float] | None: ...

    def put(
        self,
        text_hash: str,
        model_id: str,
        model_revision: str,
        *,
        vector: list[float],
    ) -> None: ...


EmbedFn = Callable[[list[str]], list[list[float]]]
IndexLookup = Mapping[tuple[str, str, str], list[float]]
ReuseSource = Literal["index", "cache", "encode"]


@dataclass(frozen=True, slots=True)
class EmbedUnit:
    """One chunk to embed; identical text across documents still yields separate units."""

    unit_id: str
    document_id: str
    embedded_text: str


@dataclass(frozen=True, slots=True)
class ResolvedEmbedding:
    unit_id: str
    document_id: str
    text_hash: str
    vector: list[float]
    source: ReuseSource


def compute_text_hash(embedded_text: str) -> str:
    """sha256 hex digest of the exact embedded text bytes (UTF-8)."""
    return hashlib.sha256(embedded_text.encode("utf-8")).hexdigest()


def resolve_embeddings(
    units: Sequence[EmbedUnit],
    *,
    model_id: str,
    model_revision: str,
    cache: EmbeddingCacheLike,
    index_lookup: IndexLookup | None = None,
    embed_fn: EmbedFn,
) -> tuple[list[ResolvedEmbedding], int]:
    """Resolve dense vectors: index → EmbeddingCache → batch encode misses.

    Returns (resolved_per_unit, encode_batch_count).
    Identical text in different documents reuses the vector but keeps separate units.
    """
    index = index_lookup or {}
    resolved: list[ResolvedEmbedding | None] = [None] * len(units)
    miss_indices: list[int] = []
    miss_texts: list[str] = []
    miss_hashes: list[str] = []

    for i, unit in enumerate(units):
        th = compute_text_hash(unit.embedded_text)
        key = (th, model_id, model_revision)
        from_index = index.get(key)
        if from_index is not None:
            resolved[i] = ResolvedEmbedding(
                unit_id=unit.unit_id,
                document_id=unit.document_id,
                text_hash=th,
                vector=list(from_index),
                source="index",
            )
            continue
        from_cache = cache.get(th, model_id, model_revision)
        if from_cache is not None:
            resolved[i] = ResolvedEmbedding(
                unit_id=unit.unit_id,
                document_id=unit.document_id,
                text_hash=th,
                vector=list(from_cache),
                source="cache",
            )
            continue
        miss_indices.append(i)
        miss_texts.append(unit.embedded_text)
        miss_hashes.append(th)

    encode_batches = 0
    if miss_texts:
        # Deduplicate encode payloads while preserving one vector per miss slot.
        unique_texts: list[str] = []
        unique_hashes: list[str] = []
        text_to_unique: dict[str, int] = {}
        for text, th in zip(miss_texts, miss_hashes, strict=True):
            if text not in text_to_unique:
                text_to_unique[text] = len(unique_texts)
                unique_texts.append(text)
                unique_hashes.append(th)
        vectors = embed_fn(unique_texts)
        encode_batches = 1
        for _text, th, vector in zip(unique_texts, unique_hashes, vectors, strict=True):
            cache.put(th, model_id, model_revision, vector=list(vector))
        for slot, text in zip(miss_indices, miss_texts, strict=True):
            unit = units[slot]
            uniq = text_to_unique[text]
            resolved[slot] = ResolvedEmbedding(
                unit_id=unit.unit_id,
                document_id=unit.document_id,
                text_hash=unique_hashes[uniq],
                vector=list(vectors[uniq]),
                source="encode",
            )

    out = [item for item in resolved if item is not None]
    if len(out) != len(units):
        raise RuntimeError("embedding resolution incomplete")
    return out, encode_batches
