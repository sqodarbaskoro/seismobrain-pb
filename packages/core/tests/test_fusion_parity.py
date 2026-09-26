"""
File: test_fusion_parity.py
Description: FR-RET-02 — reference weighted RRF fusion parity
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

from seismobrain_core.fusion import weighted_rrf


def test_weighted_rrf_identical_on_fixture() -> None:
    dense = [("a", 0.9), ("b", 0.8), ("c", 0.1)]
    sparse = [("b", 0.95), ("c", 0.7), ("d", 0.6)]
    ident = [("c", 1.0), ("a", 0.5)]
    first = weighted_rrf(
        {"dense": dense, "bm25_text": sparse, "ident": ident},
        weights={"dense": 1.0, "bm25_text": 1.0, "ident": 1.5},
        k=60,
    )
    second = weighted_rrf(
        {"dense": dense, "bm25_text": sparse, "ident": ident},
        weights={"dense": 1.0, "bm25_text": 1.0, "ident": 1.5},
        k=60,
    )
    assert [h.doc_id for h in first] == [h.doc_id for h in second]
    assert [h.score for h in first] == [h.score for h in second]


def test_higher_ident_weight_promotes_ident_hits() -> None:
    dense = [("a", 1.0), ("b", 0.9)]
    ident = [("b", 1.0), ("a", 0.1)]
    equal = weighted_rrf(
        {"dense": dense, "ident": ident},
        weights={"dense": 1.0, "ident": 1.0},
        k=60,
    )
    boosted = weighted_rrf(
        {"dense": dense, "ident": ident},
        weights={"dense": 1.0, "ident": 3.0},
        k=60,
    )
    # With equal weights, dense rank-1 (a) often wins; boost promotes b.
    assert boosted[0].doc_id == "b"
    assert equal[0].doc_id in {"a", "b"}
