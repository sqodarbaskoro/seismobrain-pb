"""
File: test_sparse_term_registry_alloc.py
Description: FR-IDX-08 — collision-free sparse term registry allocation
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

from seismobrain_core.sparse_term_registry import InMemorySparseTermRegistry


def test_distinct_tokens_never_share_index() -> None:
    registry = InMemorySparseTermRegistry()
    a = registry.get_or_assign("enc-v1", "bm25_text", "alpha")
    b = registry.get_or_assign("enc-v1", "bm25_text", "beta")
    c = registry.get_or_assign("enc-v1", "bm25_text", "gamma")
    assert len({a, b, c}) == 3


def test_same_token_returns_stable_index() -> None:
    registry = InMemorySparseTermRegistry()
    first = registry.get_or_assign("enc-v1", "bm25_text", "well")
    second = registry.get_or_assign("enc-v1", "bm25_text", "well")
    assert first == second


def test_indices_are_sequential_per_encoder_arm() -> None:
    registry = InMemorySparseTermRegistry()
    idxs = [
        registry.get_or_assign("enc-v1", "bm25_text", t)
        for t in ("a", "b", "c")
    ]
    assert idxs == [0, 1, 2]


def test_encoder_versions_isolate_allocations() -> None:
    registry = InMemorySparseTermRegistry()
    v1 = registry.get_or_assign("enc-v1", "bm25_text", "alpha")
    v2 = registry.get_or_assign("enc-v2", "bm25_text", "alpha")
    # Same token may reuse numeric idx across versions; mappings are independent.
    assert v1 == 0
    assert v2 == 0
    other = registry.get_or_assign("enc-v1", "bm25_text", "beta")
    assert other != v1
    assert registry.get_or_assign("enc-v1", "bm25_text", "alpha") == v1


def test_arms_isolate_allocations() -> None:
    registry = InMemorySparseTermRegistry()
    text_idx = registry.get_or_assign("enc-v1", "bm25_text", "p2-94")
    ident_idx = registry.get_or_assign("enc-v1", "ident", "p2-94")
    assert text_idx == 0
    assert ident_idx == 0
    assert registry.get_or_assign("enc-v1", "ident", "p2-94") == ident_idx


def test_lookup_drops_missing_query_tokens() -> None:
    registry = InMemorySparseTermRegistry()
    registry.get_or_assign("enc-v1", "bm25_text", "known")
    assert registry.lookup("enc-v1", "bm25_text", "known") == 0
    assert registry.lookup("enc-v1", "bm25_text", "unknown") is None


def test_no_hash_collision_for_many_tokens() -> None:
    registry = InMemorySparseTermRegistry()
    assigned: dict[str, int] = {}
    for i in range(500):
        token = f"term_{i}"
        idx = registry.get_or_assign("enc-v1", "bm25_text", token)
        assigned[token] = idx
    assert len(set(assigned.values())) == 500
    assert len(set(assigned.keys())) == 500
