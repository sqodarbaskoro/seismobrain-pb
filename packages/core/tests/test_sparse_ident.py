"""
File: test_sparse_ident.py
Description: FR-IDX-02 — ident sparse encoder per PRD §8.4.1
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

from seismobrain_core.sparse_ident import (
    encode_ident,
    extract_identifiers,
    has_identifiers,
)
from seismobrain_core.sparse_term_registry import InMemorySparseTermRegistry


def test_extracts_compound_identifiers_case_folded_punctuation_preserved() -> None:
    ids = extract_identifiers("Replace gasket P2/94 before restart")
    assert "p2/94" in ids


def test_emits_punctuation_stripped_variant() -> None:
    ids = extract_identifiers("code P2/94")
    assert "p2/94" in ids
    assert "p294" in ids


def test_extracts_all_caps_acronyms_of_two_plus() -> None:
    ids = extract_identifiers("Check the HSE and API guidance")
    assert "hse" in ids
    assert "api" in ids
    assert "the" not in ids
    assert "check" not in ids


def test_extracts_ip_addresses() -> None:
    ids = extract_identifiers("Host 10.0.0.15 failed")
    assert "10.0.0.15" in ids
    assert "100015" in ids  # punctuation-stripped variant


def test_no_stemming_on_ident_tokens() -> None:
    ids = extract_identifiers("sensor WELL-ALPHA-12")
    assert "well-alpha-12" in ids
    assert "wellalpha12" in ids
    # Must not stem identifier parts into NL stems.
    assert "run" not in ids


def test_ordinary_prose_without_identifiers_is_empty() -> None:
    assert extract_identifiers("the pump is running well today") == []
    assert has_identifiers("the pump is running well today") is False
    assert has_identifiers("error E-404 on unit") is True


def test_encode_ident_uses_binary_tf_and_registry() -> None:
    registry = InMemorySparseTermRegistry()
    vec = encode_ident(
        "Fault P2/94 and P2/94 again",
        registry=registry,
        encoder_version="id-bm25@1",
    )
    assert len(vec.indices) >= 2
    assert all(v == 1.0 for v in vec.values)
    assert registry.lookup("id-bm25@1", "ident", "p2/94") is not None
    assert registry.lookup("id-bm25@1", "ident", "p294") is not None
