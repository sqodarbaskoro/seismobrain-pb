"""
File: test_embedding_reuse.py
Description: FR-IDX-04 — embedding reuse by text_hash; separate points; cache bound
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

from seismobrain_core.embedding_reuse import (
    EmbedUnit,
    compute_text_hash,
    resolve_embeddings,
)


class _BoundCache:
    """Minimal in-memory cache with a hard size bound for reuse tests."""

    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        self._store: dict[tuple[str, str, str], list[float]] = {}
        self._order: list[tuple[str, str, str]] = []

    def get(
        self, text_hash: str, model_id: str, model_revision: str
    ) -> list[float] | None:
        return self._store.get((text_hash, model_id, model_revision))

    def put(
        self,
        text_hash: str,
        model_id: str,
        model_revision: str,
        *,
        vector: list[float],
    ) -> None:
        key = (text_hash, model_id, model_revision)
        self._store[key] = list(vector)
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)
        while self.size_bytes() > self.max_bytes and self._order:
            old = self._order.pop(0)
            self._store.pop(old, None)

    def size_bytes(self) -> int:
        # 4 bytes per float32 element (approximate bound accounting).
        return sum(len(v) * 4 for v in self._store.values())


def test_text_hash_is_sha256_of_embedded_text() -> None:
    text = "Document: X | Revision: 1 | Section: A\nbody"
    assert compute_text_hash(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_identical_text_different_documents_reuse_vector_separate_units() -> None:
    cache = _BoundCache(max_bytes=10_000)
    encode_calls: list[list[str]] = []

    def embed_fn(texts: list[str]) -> list[list[float]]:
        encode_calls.append(list(texts))
        return [[float(len(t)), 1.0] for t in texts]

    units = [
        EmbedUnit(unit_id="c1", document_id="doc-a", embedded_text="same body"),
        EmbedUnit(unit_id="c2", document_id="doc-b", embedded_text="same body"),
    ]
    resolved, batches = resolve_embeddings(
        units,
        model_id="m1",
        model_revision="r1",
        cache=cache,
        index_lookup={},
        embed_fn=embed_fn,
    )
    assert batches == 1
    assert len(encode_calls) == 1
    assert encode_calls[0] == ["same body"]  # encoded once
    assert len(resolved) == 2
    assert resolved[0].unit_id == "c1" and resolved[0].document_id == "doc-a"
    assert resolved[1].unit_id == "c2" and resolved[1].document_id == "doc-b"
    assert resolved[0].vector == resolved[1].vector
    assert resolved[0].text_hash == resolved[1].text_hash == compute_text_hash("same body")
    # Separate point identities preserved (two units / two future points).
    assert {resolved[0].unit_id, resolved[1].unit_id} == {"c1", "c2"}


def test_index_lookup_preferred_over_cache_and_encode() -> None:
    cache = _BoundCache(max_bytes=10_000)
    th = compute_text_hash("hit")
    index_vec = [9.0, 9.0]

    def embed_fn(texts: list[str]) -> list[list[float]]:
        raise AssertionError(f"should not encode: {texts}")

    resolved, batches = resolve_embeddings(
        [EmbedUnit(unit_id="c1", document_id="d1", embedded_text="hit")],
        model_id="m1",
        model_revision="r1",
        cache=cache,
        index_lookup={(th, "m1", "r1"): index_vec},
        embed_fn=embed_fn,
    )
    assert batches == 0
    assert resolved[0].source == "index"
    assert resolved[0].vector == index_vec


def test_cache_size_stays_within_bound() -> None:
    # Each vector is 8 floats → 32 bytes; cap allows only one entry.
    cache = _BoundCache(max_bytes=32)

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[float(i)] * 8 for i, _ in enumerate(texts)]

    resolve_embeddings(
        [EmbedUnit(unit_id="a", document_id="d", embedded_text="first")],
        model_id="m",
        model_revision="r",
        cache=cache,
        embed_fn=embed_fn,
    )
    assert cache.size_bytes() <= 32
    resolve_embeddings(
        [EmbedUnit(unit_id="b", document_id="d", embedded_text="second")],
        model_id="m",
        model_revision="r",
        cache=cache,
        embed_fn=embed_fn,
    )
    assert cache.size_bytes() <= 32
    assert cache.get(compute_text_hash("first"), "m", "r") is None
    assert cache.get(compute_text_hash("second"), "m", "r") is not None
