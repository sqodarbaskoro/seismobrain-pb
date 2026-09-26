"""
File: test_dual_query_fusion.py
Description: FR-QRY-06 — original and rewritten queries both retrieved and fused
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

from seismobrain_core.dual_query import dual_retrieve_and_fuse


def test_original_and_rewritten_both_retrieved_and_fused() -> None:
    calls: list[str] = []

    def retrieve(query: str) -> list[tuple[str, float]]:
        calls.append(query)
        if query == "original":
            return [("a", 0.9), ("b", 0.5)]
        return [("b", 0.8), ("c", 0.7)]

    fused = dual_retrieve_and_fuse(
        original="original",
        rewritten="rewritten",
        retrieve=retrieve,
    )
    assert calls == ["original", "rewritten"]
    # RRF-style: both arms contribute; b appears in both.
    ids = [item.doc_id for item in fused]
    assert ids[0] == "b"
    assert set(ids) == {"a", "b", "c"}


def test_identical_queries_retrieve_once() -> None:
    calls: list[str] = []

    def retrieve(query: str) -> list[tuple[str, float]]:
        calls.append(query)
        return [("a", 1.0)]

    fused = dual_retrieve_and_fuse(
        original="same",
        rewritten="same",
        retrieve=retrieve,
    )
    assert calls == ["same"]
    assert [item.doc_id for item in fused] == ["a"]
