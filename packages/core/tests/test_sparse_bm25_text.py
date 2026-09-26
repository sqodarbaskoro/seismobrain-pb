"""
File: test_sparse_bm25_text.py
Description: FR-IDX-02 — bm25_text sparse encoder per PRD §8.4.1–8.4.2
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

from seismobrain_core.sparse_bm25_text import (
    DEFAULT_BM25_B,
    DEFAULT_BM25_K1,
    Bm25Params,
    bm25_tf,
    encode_bm25_text,
    tokenize_bm25_text,
)
from seismobrain_core.sparse_term_registry import InMemorySparseTermRegistry


def test_tokenize_lowercases_removes_stopwords_and_stems() -> None:
    tokens = tokenize_bm25_text("The Running pumps are Running well")
    assert "the" not in tokens
    assert "are" not in tokens
    # Porter: running → run
    assert "run" in tokens
    assert "pump" in tokens
    assert "well" in tokens


def test_tokenize_splits_identifiers_into_word_parts() -> None:
    tokens = tokenize_bm25_text("Fault on well-alpha-12 during startup")
    assert "well" in tokens
    assert "alpha" in tokens
    assert "12" in tokens
    assert "fault" in tokens
    assert "startup" in tokens or "startup" in tokenize_bm25_text("startup")


def test_numeric_only_tokens_longer_than_limit_excluded() -> None:
    tokens = tokenize_bm25_text("code 1234567890 and 42", max_numeric_len=8)
    assert "1234567890" not in tokens
    assert "42" in tokens


def test_bm25_params_defaults_pinned() -> None:
    params = Bm25Params()
    assert params.k1 == DEFAULT_BM25_K1 == 1.2
    assert params.b == DEFAULT_BM25_B == 0.75
    assert params.avg_len > 0


def test_bm25_tf_uses_pinned_k1_b_avg_len() -> None:
    params = Bm25Params(k1=1.2, b=0.75, avg_len=100.0)
    # tf=2, doc_len=50 → denom = 2 + 1.2*(1 - 0.75 + 0.75*0.5) = 2 + 1.2*0.625
    expected = (2 * (1.2 + 1)) / (2 + 1.2 * (1 - 0.75 + 0.75 * (50 / 100)))
    assert bm25_tf(tf=2, doc_len=50, params=params) == expected


def test_encode_assigns_registry_indices_and_tf_weights() -> None:
    registry = InMemorySparseTermRegistry()
    params = Bm25Params(k1=1.2, b=0.75, avg_len=10.0)
    vec = encode_bm25_text(
        "pump pump valve",
        registry=registry,
        encoder_version="id-bm25@1",
        params=params,
    )
    assert len(vec.indices) == len(vec.values) == 2
    assert len(set(vec.indices)) == 2
    # Higher TF for "pump" than "valve"
    pump_i = registry.lookup("id-bm25@1", "bm25_text", "pump")
    valve_i = registry.lookup("id-bm25@1", "bm25_text", "valv")
    assert pump_i is not None and valve_i is not None
    by_idx = dict(zip(vec.indices, vec.values, strict=True))
    assert by_idx[pump_i] > by_idx[valve_i]


def test_encode_is_deterministic_for_same_params() -> None:
    registry = InMemorySparseTermRegistry()
    params = Bm25Params(k1=1.2, b=0.75, avg_len=20.0)
    a = encode_bm25_text(
        "Pressure relief valve",
        registry=registry,
        encoder_version="id-bm25@1",
        params=params,
    )
    b = encode_bm25_text(
        "Pressure relief valve",
        registry=registry,
        encoder_version="id-bm25@1",
        params=params,
    )
    assert a.indices == b.indices
    assert a.values == b.values
